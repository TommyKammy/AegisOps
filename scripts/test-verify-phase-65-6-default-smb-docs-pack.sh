#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-6-default-smb-docs-pack.sh"

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
  copy_repo_path "${target}" "docs/phase-65-6-default-smb-documentation-pack.md"
  copy_repo_path "${target}" "docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml"
  copy_repo_path "${target}" "docs/phase-65-1-release-bundle-inventory.md"
  copy_repo_path "${target}" "docs/phase-65-2-offline-install-bundle-contract.md"
  copy_repo_path "${target}" "docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
  copy_repo_path "${target}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  copy_repo_path "${target}" "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  copy_repo_path "${target}" "docs/phase-58-3-backup-command-contract.md"
  copy_repo_path "${target}" "docs/phase-58-4-restore-dry-run-contract.md"
  copy_repo_path "${target}" "docs/phase-58-5-upgrade-rollback-plan-contract.md"
  copy_repo_path "${target}" "docs/phase-58-6-support-bundle-redaction-contract.md"
  copy_repo_path "${target}" "docs/phase-59-3-ai-trace-lifecycle-contract.md"
  copy_repo_path "${target}" "docs/phase-59-4-ai-disabled-degraded-mode-contract.md"
  copy_repo_path "${target}" "docs/phase-61-minimum-source-catalog-contract.md"
  copy_repo_path "${target}" "docs/phase-62-reviewed-automation-catalog-contract.md"
  copy_repo_path "${target}" "docs/phase-62-5-manual-fallback-contract.md"
  copy_repo_path "${target}" "docs/deployment/first-user-stack.md"
  copy_repo_path "${target}" "docs/deployment/operator-training-handoff-packet.md"
  copy_repo_path "${target}" "docs/runbook.md"
  copy_repo_path "${target}" "docs/source-onboarding-contract.md"
  copy_repo_path "${target}" "scripts/verify-phase-65-6-default-smb-docs-pack.sh"
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
rm "${missing_doc_repo}/docs/phase-65-6-default-smb-documentation-pack.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 65.6 default SMB documentation pack"

missing_manifest_repo="${workdir}/missing-manifest"
create_valid_repo "${missing_manifest_repo}"
rm "${missing_manifest_repo}/docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml"
assert_fails_with "${missing_manifest_repo}" "Missing Phase 65.6 default SMB documentation pack manifest"

missing_readme_repo="${workdir}/missing-readme"
create_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 65\.6 default SMB documentation pack\]\(docs\/phase-65-6-default-smb-documentation-pack\.md\)[^\n]*\n//m' "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical cross-phase boundary bullet"

missing_install_topic_repo="${workdir}/missing-install-topic"
create_valid_repo "${missing_install_topic_repo}"
perl -0pi -e 's/\n  - topic: installation\n    owner: Platform maintainers\n    primary_reference: docs\/phase-65-2-offline-install-bundle-contract\.md\n    supporting_reference: docs\/deployment\/first-user-stack\.md\n    beta_scope: beta-design-partner-install-guidance-only\n    boundary_note: Installation docs do not prove clean-host success, RC readiness, GA readiness, or production installer completeness\.//m' "${missing_install_topic_repo}/docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml"
assert_fails_with "${missing_install_topic_repo}" "Missing Phase 65.6 docs pack topic: installation"

missing_daily_ops_doc_repo="${workdir}/missing-daily-ops-doc"
create_valid_repo "${missing_daily_ops_doc_repo}"
rm "${missing_daily_ops_doc_repo}/docs/runbook.md"
assert_fails_with "${missing_daily_ops_doc_repo}" "Missing Phase 65.6 docs pack referenced file for daily-operation: docs/runbook.md"

missing_source_onboarding_doc_repo="${workdir}/missing-source-onboarding-doc"
create_valid_repo "${missing_source_onboarding_doc_repo}"
rm "${missing_source_onboarding_doc_repo}/docs/source-onboarding-contract.md"
assert_fails_with "${missing_source_onboarding_doc_repo}" "Missing Phase 65.6 docs pack referenced file for source-onboarding: docs/source-onboarding-contract.md"

missing_automation_doc_repo="${workdir}/missing-automation-doc"
create_valid_repo "${missing_automation_doc_repo}"
rm "${missing_automation_doc_repo}/docs/phase-62-reviewed-automation-catalog-contract.md"
assert_fails_with "${missing_automation_doc_repo}" "Missing Phase 65.6 docs pack referenced file for automation-catalog: docs/phase-62-reviewed-automation-catalog-contract.md"

missing_ai_doc_repo="${workdir}/missing-ai-doc"
create_valid_repo "${missing_ai_doc_repo}"
rm "${missing_ai_doc_repo}/docs/phase-59-3-ai-trace-lifecycle-contract.md"
assert_fails_with "${missing_ai_doc_repo}" "Missing Phase 65.6 docs pack referenced file for ai-usage: docs/phase-59-3-ai-trace-lifecycle-contract.md"

missing_backup_restore_doc_repo="${workdir}/missing-backup-restore-doc"
create_valid_repo "${missing_backup_restore_doc_repo}"
rm "${missing_backup_restore_doc_repo}/docs/phase-58-4-restore-dry-run-contract.md"
assert_fails_with "${missing_backup_restore_doc_repo}" "Missing Phase 65.6 docs pack referenced file for backup-and-restore: docs/phase-58-4-restore-dry-run-contract.md"

missing_support_bundle_doc_repo="${workdir}/missing-support-bundle-doc"
create_valid_repo "${missing_support_bundle_doc_repo}"
rm "${missing_support_bundle_doc_repo}/docs/phase-58-6-support-bundle-redaction-contract.md"
assert_fails_with "${missing_support_bundle_doc_repo}" "Missing Phase 58.6 support bundle contract reference"

missing_upgrade_rollback_doc_repo="${workdir}/missing-upgrade-rollback-doc"
create_valid_repo "${missing_upgrade_rollback_doc_repo}"
rm "${missing_upgrade_rollback_doc_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_fails_with "${missing_upgrade_rollback_doc_repo}" "Missing Phase 58.5 upgrade rollback contract reference"

unquoted_approval_repo="${workdir}/unquoted-approval"
create_valid_repo "${unquoted_approval_repo}"
perl -0pi -e 's/^approval_record:.*/approval_record: issue #1385/m' "${unquoted_approval_repo}/docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml"
assert_fails_with "${unquoted_approval_repo}" "approval_record must quote issue #1385"

duplicate_topics_repo="${workdir}/duplicate-topics"
create_valid_repo "${duplicate_topics_repo}"
cat >>"${duplicate_topics_repo}/docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml" <<'EOF_DUPLICATE_TOPICS'
topics:
  - topic: installation
    owner: todo
    primary_reference: todo
    supporting_reference: todo
    beta_scope: todo
    boundary_note: todo
EOF_DUPLICATE_TOPICS
assert_fails_with "${duplicate_topics_repo}" "duplicate top-level field: topics"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
workstation_path="/""Users/example/docs-pack.md"
WORKSTATION_PATH="${workstation_path}" perl -0pi -e 's#docs/runbook\.md#$ENV{WORKSTATION_PATH}#m' "${workstation_path_repo}/docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml"
assert_fails_with "${workstation_path_repo}" "Invalid Phase 65.6 docs pack"

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
printf '%s\n' "token = abc123" >>"${secret_repo}/docs/phase-65-6-default-smb-documentation-pack.md"
assert_fails_with "${secret_repo}" "production secret material"

customer_private_repo="${workdir}/customer-private"
create_valid_repo "${customer_private_repo}"
printf '%s\n' "The docs pack includes customer-private example data." >>"${customer_private_repo}/docs/phase-65-6-default-smb-documentation-pack.md"
assert_fails_with "${customer_private_repo}" "customer-private data"

rc_overclaim_repo="${workdir}/rc-overclaim"
create_valid_repo "${rc_overclaim_repo}"
printf '%s\n' "Phase 65.6 documentation pack proves RC readiness." >>"${rc_overclaim_repo}/docs/phase-65-6-default-smb-documentation-pack.md"
assert_fails_with "${rc_overclaim_repo}" "readiness, support, or gate overclaim"

ga_overclaim_repo="${workdir}/ga-overclaim"
create_valid_repo "${ga_overclaim_repo}"
printf '%s\n' "The SMB docs pack confirms GA readiness." >>"${ga_overclaim_repo}/docs/phase-65-6-default-smb-documentation-pack.md"
assert_fails_with "${ga_overclaim_repo}" "readiness, support, or gate overclaim"

production_support_overclaim_repo="${workdir}/production-support-overclaim"
create_valid_repo "${production_support_overclaim_repo}"
printf '%s\n' "Phase 65.6 documentation pack grants production support readiness." >>"${production_support_overclaim_repo}/docs/phase-65-6-default-smb-documentation-pack.md"
assert_fails_with "${production_support_overclaim_repo}" "readiness, support, or gate overclaim"

verifier_truth_repo="${workdir}/verifier-truth"
create_valid_repo "${verifier_truth_repo}"
printf '%s\n' "The verifier output becomes readiness truth." >>"${verifier_truth_repo}/docs/phase-65-6-default-smb-documentation-pack.md"
assert_fails_with "${verifier_truth_repo}" "verifier or issue-lint truth shortcut"

echo "Phase 65.6 default SMB documentation pack verifier self-test passed"
