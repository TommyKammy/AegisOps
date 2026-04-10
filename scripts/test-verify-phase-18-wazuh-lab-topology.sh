#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-18-wazuh-lab-topology.sh"
canonical_design_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
canonical_validation_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-validation.md"
canonical_asset_doc="${repo_root}/docs/phase-18-wazuh-single-node-lab-assets.md"
canonical_phase17_doc="${repo_root}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
canonical_phase16_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
canonical_wazuh_contract_doc="${repo_root}/docs/wazuh-alert-ingest-contract.md"
canonical_source_contract_doc="${repo_root}/docs/source-onboarding-contract.md"
canonical_github_audit_doc="${repo_root}/docs/source-families/github-audit/onboarding-package.md"
canonical_architecture_doc="${repo_root}/docs/architecture.md"
canonical_asset_readme="${repo_root}/ingest/wazuh/single-node-lab/README.md"
canonical_asset_bootstrap="${repo_root}/ingest/wazuh/single-node-lab/bootstrap.env.sample"
canonical_asset_compose="${repo_root}/ingest/wazuh/single-node-lab/docker-compose.yml"
canonical_asset_integration="${repo_root}/ingest/wazuh/single-node-lab/ossec.integration.sample.xml"
canonical_asset_render_helper="${repo_root}/ingest/wazuh/single-node-lab/render-ossec-integration.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/source-families/github-audit" "${target}/scripts" "${target}/ingest/wazuh/single-node-lab"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_canonical_artifacts() {
  local target="$1"

  cp "${canonical_design_doc}" "${target}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
  cp "${canonical_validation_doc}" "${target}/docs/phase-18-wazuh-lab-topology-validation.md"
  cp "${canonical_asset_doc}" "${target}/docs/phase-18-wazuh-single-node-lab-assets.md"
  cp "${canonical_phase17_doc}" "${target}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  cp "${canonical_phase16_doc}" "${target}/docs/phase-16-release-state-and-first-boot-scope.md"
  cp "${canonical_wazuh_contract_doc}" "${target}/docs/wazuh-alert-ingest-contract.md"
  cp "${canonical_source_contract_doc}" "${target}/docs/source-onboarding-contract.md"
  cp "${canonical_github_audit_doc}" "${target}/docs/source-families/github-audit/onboarding-package.md"
  cp "${canonical_architecture_doc}" "${target}/docs/architecture.md"
  cp "${canonical_asset_readme}" "${target}/ingest/wazuh/single-node-lab/README.md"
  cp "${canonical_asset_bootstrap}" "${target}/ingest/wazuh/single-node-lab/bootstrap.env.sample"
  cp "${canonical_asset_compose}" "${target}/ingest/wazuh/single-node-lab/docker-compose.yml"
  cp "${canonical_asset_integration}" "${target}/ingest/wazuh/single-node-lab/ossec.integration.sample.xml"
  cp "${canonical_asset_render_helper}" "${target}/ingest/wazuh/single-node-lab/render-ossec-integration.sh"
  cp "${verifier}" "${target}/scripts/verify-phase-18-wazuh-lab-topology.sh"
  cp "${repo_root}/scripts/test-verify-phase-18-wazuh-lab-topology.sh" "${target}/scripts/test-verify-phase-18-wazuh-lab-topology.sh"
  git -C "${target}" add .
}

remove_text_from_doc() {
  local target="$1"
  local doc_path="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${doc_path}"
  git -C "${target}" add "${doc_path}"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_canonical_artifacts "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_design_repo="${workdir}/missing-design"
create_repo "${missing_design_repo}"
write_canonical_artifacts "${missing_design_repo}"
rm "${missing_design_repo}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
git -C "${missing_design_repo}" add -u
commit_fixture "${missing_design_repo}"
assert_fails_with "${missing_design_repo}" "Missing Phase 18 Wazuh lab topology doc:"

missing_live_path_repo="${workdir}/missing-live-path"
create_repo "${missing_live_path_repo}"
write_canonical_artifacts "${missing_live_path_repo}"
remove_text_from_doc "${missing_live_path_repo}" "${missing_live_path_repo}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md" 'The approved live path is Wazuh -> AegisOps.'
commit_fixture "${missing_live_path_repo}"
assert_fails_with "${missing_live_path_repo}" 'The approved live path is Wazuh -> AegisOps.'

missing_auth_repo="${workdir}/missing-auth"
create_repo "${missing_auth_repo}"
write_canonical_artifacts "${missing_auth_repo}"
remove_text_from_doc "${missing_auth_repo}" "${missing_auth_repo}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md" 'The reviewed request authentication contract is `Authorization: Bearer <shared secret>`.'
commit_fixture "${missing_auth_repo}"
assert_fails_with "${missing_auth_repo}" 'The reviewed request authentication contract is `Authorization: Bearer <shared secret>`.'

missing_deferred_scope_repo="${workdir}/missing-deferred-scope"
create_repo "${missing_deferred_scope_repo}"
write_canonical_artifacts "${missing_deferred_scope_repo}"
remove_text_from_doc "${missing_deferred_scope_repo}" "${missing_deferred_scope_repo}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md" '- guarded automation live wiring;'
commit_fixture "${missing_deferred_scope_repo}"
assert_fails_with "${missing_deferred_scope_repo}" '- guarded automation live wiring;'

missing_validation_note_repo="${workdir}/missing-validation-note"
create_repo "${missing_validation_note_repo}"
write_canonical_artifacts "${missing_validation_note_repo}"
remove_text_from_doc "${missing_validation_note_repo}" "${missing_validation_note_repo}/docs/phase-18-wazuh-lab-topology-validation.md" 'Confirmed the live ingest path remains fail-closed by rejecting non-HTTPS requests, non-POST requests, missing or invalid bearer credentials, direct backend bypass attempts, invalid JSON payloads, Wazuh payloads that violate required field expectations, and payloads outside the approved first live family.'
commit_fixture "${missing_validation_note_repo}"
assert_fails_with "${missing_validation_note_repo}" 'Confirmed the live ingest path remains fail-closed by rejecting non-HTTPS requests, non-POST requests, missing or invalid bearer credentials, direct backend bypass attempts, invalid JSON payloads, Wazuh payloads that violate required field expectations, and payloads outside the approved first live family.'

missing_asset_doc_repo="${workdir}/missing-asset-doc"
create_repo "${missing_asset_doc_repo}"
write_canonical_artifacts "${missing_asset_doc_repo}"
rm "${missing_asset_doc_repo}/docs/phase-18-wazuh-single-node-lab-assets.md"
git -C "${missing_asset_doc_repo}" add -u
commit_fixture "${missing_asset_doc_repo}"
assert_fails_with "${missing_asset_doc_repo}" "Missing Phase 18 Wazuh lab asset doc:"

missing_asset_compose_repo="${workdir}/missing-asset-compose"
create_repo "${missing_asset_compose_repo}"
write_canonical_artifacts "${missing_asset_compose_repo}"
remove_text_from_doc "${missing_asset_compose_repo}" "${missing_asset_compose_repo}/ingest/wazuh/single-node-lab/docker-compose.yml" '    # GitHub audit remains the only approved first live source family.'
commit_fixture "${missing_asset_compose_repo}"
assert_fails_with "${missing_asset_compose_repo}" '    # GitHub audit remains the only approved first live source family.'

published_ports_repo="${workdir}/published-ports"
create_repo "${published_ports_repo}"
write_canonical_artifacts "${published_ports_repo}"
perl -0pi -e 's/    expose:\n      - "1514\/udp"\n      - "1515"\n      - "55000"/    expose:\n      - "1514\/udp"\n      - "1515"\n      - "55000"\n    ports:\n      - "1514:1514\/udp"\n      - "1515:1515"\n      - "55000:55000"/' "${published_ports_repo}/ingest/wazuh/single-node-lab/docker-compose.yml"
git -C "${published_ports_repo}" add ingest/wazuh/single-node-lab/docker-compose.yml
commit_fixture "${published_ports_repo}"
assert_fails_with "${published_ports_repo}" 'Phase 18 Wazuh lab compose asset must not publish host ports directly.'

missing_group_repo="${workdir}/missing-group"
create_repo "${missing_group_repo}"
write_canonical_artifacts "${missing_group_repo}"
remove_text_from_doc "${missing_group_repo}" "${missing_group_repo}/ingest/wazuh/single-node-lab/ossec.integration.sample.xml" '  <group>github_audit</group>'
commit_fixture "${missing_group_repo}"
assert_fails_with "${missing_group_repo}" '  <group>github_audit</group>'

missing_deviation_repo="${workdir}/missing-deviation"
create_repo "${missing_deviation_repo}"
write_canonical_artifacts "${missing_deviation_repo}"
remove_text_from_doc "${missing_deviation_repo}" "${missing_deviation_repo}/docs/phase-18-wazuh-lab-topology-validation.md" '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
commit_fixture "${missing_deviation_repo}"
assert_fails_with "${missing_deviation_repo}" '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'

echo "Phase 18 Wazuh lab topology verifier enforces the reviewed live-path contract and deferred-scope boundaries."
