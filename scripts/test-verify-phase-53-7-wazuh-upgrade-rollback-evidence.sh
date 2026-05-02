#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-53-7-wazuh-upgrade-rollback-evidence.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/wazuh"
  printf '%s\n' "# AegisOps" "See [Phase 53.7 Wazuh upgrade rollback evidence contract](docs/deployment/wazuh-upgrade-rollback-evidence-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/wazuh-upgrade-rollback-evidence-contract.md" \
    "${target}/docs/deployment/wazuh-upgrade-rollback-evidence-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
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

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

remove_text_from_contract() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/deployment/wazuh-upgrade-rollback-evidence-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

reviewed_future_values_repo="${workdir}/reviewed-future-values"
create_valid_repo "${reviewed_future_values_repo}"
perl -0pi -e 's/^version_before:.*$/version_before: 4.12.1/m;
  s/^version_after:.*$/version_after: 4.13.0/m;
  s/^rollback_owner:.*$/rollback_owner: secops-release-review-board/m;
  s/^    version_before:.*$/    version_before: 4.12.1/mg;
  s/^    version_after:.*$/    version_after: 4.13.0/mg' \
  "${reviewed_future_values_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_passes "${reviewed_future_values_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/wazuh-upgrade-rollback-evidence-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback evidence contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "${missing_artifact_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback evidence artifact"

missing_owner_repo="${workdir}/missing-owner"
create_valid_repo "${missing_owner_repo}"
perl -0pi -e 's/^rollback_owner:.*\n//m' \
  "${missing_owner_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_owner_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback top-level rollback owner: rollback_owner"

placeholder_owner_repo="${workdir}/placeholder-owner"
create_valid_repo "${placeholder_owner_repo}"
perl -0pi -e 's/^rollback_owner:.*$/rollback_owner: TBD/m' \
  "${placeholder_owner_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${placeholder_owner_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback placeholder rollback owner: rollback_owner: TBD"

missing_version_before_repo="${workdir}/missing-version-before"
create_valid_repo "${missing_version_before_repo}"
perl -0pi -e 's/^version_before:.*\n//m' \
  "${missing_version_before_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_version_before_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback top-level version before: version_before"

floating_version_before_repo="${workdir}/floating-version-before"
create_valid_repo "${floating_version_before_repo}"
perl -0pi -e 's/^version_before:.*$/version_before: latest/m' \
  "${floating_version_before_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${floating_version_before_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback unreviewed version before: version_before: latest"

missing_version_after_repo="${workdir}/missing-version-after"
create_valid_repo "${missing_version_after_repo}"
perl -0pi -e 's/^version_after:.*\n//m' \
  "${missing_version_after_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_version_after_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback top-level version after: version_after"

rc_version_after_repo="${workdir}/rc-version-after"
create_valid_repo "${rc_version_after_repo}"
perl -0pi -e 's/^version_after:.*$/version_after: 4.13.0-rc1/m' \
  "${rc_version_after_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${rc_version_after_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback unreviewed version after: version_after: 4.13.0-rc1"

missing_trigger_repo="${workdir}/missing-trigger"
create_valid_repo "${missing_trigger_repo}"
perl -0pi -e 's/^rollback_trigger:.*\n//m' \
  "${missing_trigger_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_trigger_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback top-level rollback trigger: rollback_trigger"

placeholder_trigger_repo="${workdir}/placeholder-trigger"
create_valid_repo "${placeholder_trigger_repo}"
perl -0pi -e 's/^rollback_trigger:.*$/rollback_trigger: operator decides later/m' \
  "${placeholder_trigger_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${placeholder_trigger_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback placeholder rollback trigger: rollback_trigger: operator decides later"

missing_evidence_reference_repo="${workdir}/missing-evidence-reference"
create_valid_repo "${missing_evidence_reference_repo}"
perl -0pi -e 's/^  - aegisops-release-gate-record\n//m' \
  "${missing_evidence_reference_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_evidence_reference_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback evidence reference: aegisops-release-gate-record"

missing_known_limitation_repo="${workdir}/missing-known-limitation"
create_valid_repo "${missing_known_limitation_repo}"
perl -0pi -e 's/^  - no-full-wazuh-upgrader\n//m' \
  "${missing_known_limitation_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_known_limitation_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback known limitation: no-full-wazuh-upgrader"

prefixed_authority_key_repo="${workdir}/prefixed-authority-key"
create_valid_repo "${prefixed_authority_key_repo}"
perl -0pi -e 's/^authority_mutation_allowed: false$/disable_authority_mutation_allowed: false/m' \
  "${prefixed_authority_key_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${prefixed_authority_key_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback artifact term: authority_mutation_allowed: false"

prefixed_components_section_repo="${workdir}/prefixed-components-section"
create_valid_repo "${prefixed_components_section_repo}"
perl -0pi -e 's/^components:$/my_components:/m' \
  "${prefixed_components_section_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${prefixed_components_section_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback artifact term: components:"

missing_handoff_repo="${workdir}/missing-handoff"
create_valid_repo "${missing_handoff_repo}"
perl -0pi -e 's/^profile_change_handoff:\n(?:  .*\n)+component_evidence:/component_evidence:/m' \
  "${missing_handoff_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_handoff_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback artifact term: profile_change_handoff:"

missing_handoff_target_repo="${workdir}/missing-handoff-target"
create_valid_repo "${missing_handoff_target_repo}"
perl -0pi -e 's/^  target:.*\n//m' \
  "${missing_handoff_target_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_handoff_target_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback profile change handoff field: target"

empty_handoff_recipient_repo="${workdir}/empty-handoff-recipient"
create_valid_repo "${empty_handoff_recipient_repo}"
perl -0pi -e 's/^  recipient:.*$/  recipient:/m' \
  "${empty_handoff_recipient_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${empty_handoff_recipient_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback profile change handoff field: recipient"

missing_component_rollback_target_repo="${workdir}/missing-component-rollback-target"
create_valid_repo "${missing_component_rollback_target_repo}"
perl -0pi -e 's/^    rollback_target: last-reviewed-indexer-profile-version\n//m' \
  "${missing_component_rollback_target_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${missing_component_rollback_target_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback component evidence indexer field: rollback_target"

full_upgrader_claim_repo="${workdir}/full-upgrader-claim"
create_valid_repo "${full_upgrader_claim_repo}"
perl -0pi -e 's/full_upgrader_implemented: false/full_upgrader_implemented: true/' \
  "${full_upgrader_claim_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${full_upgrader_claim_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: full upgrader implementation claim detected"

quoted_full_upgrader_claim_repo="${workdir}/quoted-full-upgrader-claim"
create_valid_repo "${quoted_full_upgrader_claim_repo}"
perl -0pi -e 's/full_upgrader_implemented: false/full_upgrader_implemented: "True"/' \
  "${quoted_full_upgrader_claim_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${quoted_full_upgrader_claim_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: full upgrader implementation claim detected"

duplicate_full_upgrader_claim_repo="${workdir}/duplicate-full-upgrader-claim"
create_valid_repo "${duplicate_full_upgrader_claim_repo}"
perl -0pi -e 's/full_upgrader_implemented: false/full_upgrader_implemented: false\nfull_upgrader_implemented: True/' \
  "${duplicate_full_upgrader_claim_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${duplicate_full_upgrader_claim_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback duplicate top-level boolean scalar: full_upgrader_implemented"

upgrade_automation_claim_repo="${workdir}/upgrade-automation-claim"
create_valid_repo "${upgrade_automation_claim_repo}"
perl -0pi -e 's/upgrade_automation_allowed: false/upgrade_automation_allowed: true/' \
  "${upgrade_automation_claim_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${upgrade_automation_claim_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: upgrade automation claim detected"

numeric_upgrade_automation_claim_repo="${workdir}/numeric-upgrade-automation-claim"
create_valid_repo "${numeric_upgrade_automation_claim_repo}"
perl -0pi -e 's/upgrade_automation_allowed: false/upgrade_automation_allowed: 1/' \
  "${numeric_upgrade_automation_claim_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${numeric_upgrade_automation_claim_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: upgrade automation claim detected"

duplicate_upgrade_automation_claim_repo="${workdir}/duplicate-upgrade-automation-claim"
create_valid_repo "${duplicate_upgrade_automation_claim_repo}"
perl -0pi -e 's/upgrade_automation_allowed: false/upgrade_automation_allowed: false\nupgrade_automation_allowed: "true"/' \
  "${duplicate_upgrade_automation_claim_repo}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
assert_fails_with \
  "${duplicate_upgrade_automation_claim_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback duplicate top-level boolean scalar: upgrade_automation_allowed"

authority_truth_repo="${workdir}/authority-truth"
create_valid_repo "${authority_truth_repo}"
printf '%s\n' "Wazuh version state is AegisOps release truth." \
  >>"${authority_truth_repo}/docs/deployment/wazuh-upgrade-rollback-evidence-contract.md"
assert_fails_with \
  "${authority_truth_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback claim: Wazuh version state is AegisOps release truth"

missing_forbidden_claim_repo="${workdir}/missing-forbidden-claim"
create_valid_repo "${missing_forbidden_claim_repo}"
remove_text_from_contract "${missing_forbidden_claim_repo}" \
  "Phase 53.7 implements a full Wazuh upgrader."
assert_fails_with \
  "${missing_forbidden_claim_repo}" \
  "Missing Phase 53.7 Wazuh upgrade rollback forbidden claim: Phase 53.7 implements a full Wazuh upgrader"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/wazuh-upgrade-rollback-evidence-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 53.7 Wazuh upgrade rollback evidence contract."

echo "Phase 53.7 Wazuh upgrade rollback evidence verifier tests passed."
