#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-66-6-rc-supportability-proof.sh"
doc_rel="docs/phase-66-6-rc-supportability-proof.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"
base_valid_repo=""

assert_passes() {
  local target="$1"

  if ! PHASE66_6_SKIP_PATH_HYGIENE=1 bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_passes_with_path_hygiene() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier with path hygiene to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if PHASE66_6_SKIP_PATH_HYGIENE=1 bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
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

assert_fails_with_path_hygiene() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier with path hygiene to fail for ${target}" >&2
    cat "${fail_stdout}" >&2
    exit 1
  fi

  if ! grep -Fiq -- "${expected}" "${fail_stderr}"; then
    echo "Expected path-hygiene failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

copy_repo_path() {
  local target="$1"
  local relative_path="$2"

  mkdir -p "${target}/$(dirname "${relative_path}")"
  cp -p "${repo_root}/${relative_path}" "${target}/${relative_path}"
}

copy_valid_repo() {
  local target="$1"
  local path

  if [[ -n "${base_valid_repo}" && -d "${base_valid_repo}/.git" ]]; then
    mkdir -p "${target}"
    cp -R "${base_valid_repo}/." "${target}/"
    return
  fi

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "${doc_rel}"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"

  for path in \
    "docs/phase-66-1-clean-host-rc-e2e-harness.md" \
    "docs/phase-58-3-backup-command-contract.md" \
    "docs/phase-58-4-restore-dry-run-contract.md" \
    "docs/phase-58-5-upgrade-rollback-plan-contract.md" \
    "docs/phase-58-6-support-bundle-redaction-contract.md" \
    "docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "docs/phase-65-closeout-evaluation.md"; do
    copy_repo_path "${target}" "${path}"
  done

  for path in \
    "scripts/verify-phase-66-6-rc-supportability-proof.sh" \
    "scripts/test-verify-phase-66-6-rc-supportability-proof.sh" \
    "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh" \
    "scripts/verify-publishable-path-hygiene.sh"; do
    copy_repo_path "${target}" "${path}"
  done

  git -C "${target}" init -q
  git -C "${target}" config user.email "aegisops@example.invalid"
  git -C "${target}" config user.name "AegisOps Test"
  git -C "${target}" add README.md docs scripts control-plane/aegisops
  git -C "${target}" commit -q -m "fixture"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' "${target}/${doc_rel}"
}

replace_doc_text() {
  local target="$1"
  local field="$2"
  local old="$3"
  local new="$4"

  FIELD="${field}" OLD="${old}" NEW="${new}" perl -pi -e '
    if (/^\Q$ENV{FIELD}\E=/) {
      s/\Q$ENV{OLD}\E/$ENV{NEW}/;
    }
  ' "${target}/${doc_rel}"
}

append_doc_line() {
  local target="$1"
  local line="$2"

  printf '%s\n' "${line}" >>"${target}/${doc_rel}"
}

insert_before_doc_text() {
  local target="$1"
  local marker="$2"
  local text="$3"

  MARKER="${marker}" INSERT="${text}" perl -0pi -e '
    s/\Q$ENV{MARKER}\E/$ENV{INSERT}\n$ENV{MARKER}/
  ' "${target}/${doc_rel}"
}

timestamp_values="$(python3 <<'PY'
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc).replace(microsecond=0)
values = {
    "backup_created_at": now - timedelta(hours=3),
    "restore_created_at": now - timedelta(hours=2, minutes=45),
    "restore_before_backup": now - timedelta(hours=3, seconds=1),
    "bundle_created_at": now - timedelta(hours=2, minutes=30),
    "bundle_before_restore": now - timedelta(hours=2, minutes=45, seconds=1),
    "reviewed_at": now - timedelta(hours=2),
    "review_before_bundle": now - timedelta(hours=2, minutes=30, seconds=1),
    "future_reviewed_at": now + timedelta(hours=1),
}
ordered = [value.isoformat().replace("+00:00", "Z") for value in values.values()]
ordered.extend(
    (
        values["restore_before_backup"].astimezone(timezone(timedelta(hours=2))).isoformat(),
        now.date().isoformat(),
        (now.date() + timedelta(days=25)).isoformat(),
        (now.date() - timedelta(days=1)).isoformat(),
    )
)
print("|".join(ordered))
PY
)"
IFS='|' read -r backup_created_at restore_created_at restore_before_backup \
  bundle_created_at bundle_before_restore reviewed_at review_before_bundle \
  future_reviewed_at restore_before_backup_offset decision_date follow_up_date prior_date \
  <<<"${timestamp_values}"

packet_lines=(
  "journey_run_id=journey-66-1-0007"
  "repository_revision=__REPOSITORY_REVISION__"
  "backup_evidence=journey_run_id=journey-66-1-0007; repository_revision=__REPOSITORY_REVISION__; manifest_id=backup-007; custody_reference=aegisops://evidence/backup-007; created_at=${backup_created_at}; owner=group:release-ops; status=completed"
  "restore_dry_run_evidence=journey_run_id=journey-66-1-0007; repository_revision=__REPOSITORY_REVISION__; dry_run_id=restore-dry-007; evidence_reference=aegisops://evidence/restore-dry-007; backup_reference=aegisops://evidence/backup-007; target_profile=smb-single-node; created_at=${restore_created_at}; operator=group:release-ops; result=passed"
  "upgrade_plan=journey_run_id=journey-66-1-0007; repository_revision=__REPOSITORY_REVISION__; plan_id=upgrade-007; evidence_reference=aegisops://evidence/upgrade-007; version_before=1.6.0; version_after=1.7.0; target_profile=smb-single-node; preflight_result=passed:aegisops://evidence/preflight-007; evidence_links=aegisops://evidence/upgrade-detail-007"
  "rollback_plan=journey_run_id=journey-66-1-0007; repository_revision=__REPOSITORY_REVISION__; plan_id=rollback-007; evidence_reference=aegisops://evidence/rollback-007; backup_reference=aegisops://evidence/backup-007; rollback_owner=group:release-ops; rollback_trigger=failed:aegisops://evidence/post-upgrade-smoke-007; rollback_target=aegisops://evidence/backup-007"
  "support_bundle=journey_run_id=journey-66-1-0007; repository_revision=__REPOSITORY_REVISION__; bundle_id=bundle-007; evidence_reference=aegisops://evidence/bundle-007; environment_class=rc-lab; component_versions=aegisops-1.7.0; doctor_summary=aegisops://evidence/doctor-007; backup_restore_references=aegisops://evidence/backup-007,aegisops://evidence/restore-dry-007; upgrade_rollback_references=aegisops://evidence/upgrade-007,aegisops://evidence/rollback-007; created_at=${bundle_created_at}; owner=group:support-review; evidence_links=aegisops://evidence/bundle-detail-007"
  "redaction_manifest=journey_run_id=journey-66-1-0007; repository_revision=__REPOSITORY_REVISION__; manifest_id=redaction-007; evidence_reference=aegisops://evidence/redaction-007; bundle_reference=aegisops://evidence/bundle-007; scan_result=passed; secret_values=absent; workstation_paths=absent; private_payloads=redacted; ticket_private_content=absent; tokens_and_headers=absent; certs_and_keys=absent; credentials=absent; customer_identifiers=redacted; authority_boundary=subordinate-evidence-only"
  "owner_review=journey_run_id=journey-66-1-0007; repository_revision=__REPOSITORY_REVISION__; reviewer=person:release-owner; reviewed_references=aegisops://evidence/bundle-007,aegisops://evidence/redaction-007; reviewed_at=${reviewed_at}; disposition=accepted-with-follow-up; accepted_risk=bounded-rc-only; follow_up_owner=group:support-owner"
  "limitation_references=journey_run_id=journey-66-1-0007; repository_revision=__REPOSITORY_REVISION__; ids=LIM-66-006; owner=group:support-owner; decision_date=${decision_date}; follow_up_date=${follow_up_date}"
  "non_claims=rc-evidence-only,not-rc-gate-pass,not-ga,not-production-support,not-customer-portal,not-commercial-replacement,not-support-truth"
)

append_complete_packet() {
  local target="$1"
  local line
  local repository_revision

  repository_revision="$(git -C "${target}" rev-parse HEAD)"
  printf '\n## Test Proof Packet\n' >>"${target}/${doc_rel}"
  for line in "${packet_lines[@]}"; do
    printf '%s\n' "${line//__REPOSITORY_REVISION__/${repository_revision}}" >>"${target}/${doc_rel}"
  done
}

append_complete_table_packet() {
  local target="$1"
  local line
  local field
  local value
  local repository_revision

  repository_revision="$(git -C "${target}" rev-parse HEAD)"
  printf '\n## Test Table Proof Packet\n\n| Field | Value |\n| --- | --- |\n' >>"${target}/${doc_rel}"
  for line in "${packet_lines[@]}"; do
    line="${line//__REPOSITORY_REVISION__/${repository_revision}}"
    field="${line%%=*}"
    value="${line#*=}"
    printf '| `%s` | %s |\n' "${field}" "${value}" >>"${target}/${doc_rel}"
  done
}

insert_complete_table_packet_before() {
  local target="$1"
  local marker="$2"
  local line
  local field
  local value
  local repository_revision
  local packet_text=$'| Field | Value |\n| --- | --- |\n'

  repository_revision="$(git -C "${target}" rev-parse HEAD)"
  for line in "${packet_lines[@]}"; do
    line="${line//__REPOSITORY_REVISION__/${repository_revision}}"
    field="${line%%=*}"
    value="${line#*=}"
    packet_text+="| \`${field}\` | ${value} |"$'\n'
  done
  insert_before_doc_text "${target}" "${marker}" "${packet_text}"
}

mutated_packet_case() {
  local name="$1"
  local field="$2"
  local old="$3"
  local new="$4"
  local expected="$5"
  local target="${workdir}/${name}"

  copy_valid_repo "${target}"
  append_complete_packet "${target}"
  replace_doc_text "${target}" "${field}" "${old}" "${new}"
  assert_fails_with "${target}" "${expected}"
}

forbidden_claim_case() {
  local name="$1"
  local claim="$2"
  local target="${workdir}/${name}"

  copy_valid_repo "${target}"
  append_doc_line "${target}" "${claim}"
  assert_fails_with "${target}" "authority or readiness overclaim detected"
}

leak_case() {
  local name="$1"
  local value="$2"
  local expected="$3"
  local target="${workdir}/${name}"

  copy_valid_repo "${target}"
  append_doc_line "${target}" "${value}"
  assert_fails_with "${target}" "${expected}"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes_with_path_hygiene "${valid_repo}"
base_valid_repo="${valid_repo}"

assignment_packet_repo="${workdir}/assignment-packet"
copy_valid_repo "${assignment_packet_repo}"
append_complete_packet "${assignment_packet_repo}"
assert_passes "${assignment_packet_repo}"

table_packet_repo="${workdir}/table-packet"
copy_valid_repo "${table_packet_repo}"
append_complete_table_packet "${table_packet_repo}"
assert_passes "${table_packet_repo}"

evidence_section_complete_repo="${workdir}/evidence-section-complete"
copy_valid_repo "${evidence_section_complete_repo}"
insert_complete_table_packet_before \
  "${evidence_section_complete_repo}" \
  "## 3. Evidence Binding And Secret Hygiene"
assert_passes "${evidence_section_complete_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/${doc_rel}"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66.6 RC supportability proof"

missing_reference_repo="${workdir}/missing-reference"
copy_valid_repo "${missing_reference_repo}"
rm "${missing_reference_repo}/docs/phase-58-6-support-bundle-redaction-contract.md"
assert_fails_with "${missing_reference_repo}" "Missing Phase 66.6 reference docs/phase-58-6-support-bundle-redaction-contract.md"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 66\.6 RC supportability proof\][^\n]*\n//m' "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical Phase 66.6 boundary statement"

missing_static_repo="${workdir}/missing-static"
copy_valid_repo "${missing_static_repo}"
remove_doc_text "${missing_static_repo}" "This proof is RC evidence only."
assert_fails_with "${missing_static_repo}" "Missing Phase 66.6 RC supportability proof statement"

commented_static_repo="${workdir}/commented-static"
copy_valid_repo "${commented_static_repo}"
remove_doc_text "${commented_static_repo}" "This proof is RC evidence only."
append_doc_line "${commented_static_repo}" "<!-- This proof is RC evidence only. -->"
assert_fails_with "${commented_static_repo}" "Missing Phase 66.6 RC supportability proof statement"

missing_row_repo="${workdir}/missing-row"
copy_valid_repo "${missing_row_repo}"
remove_doc_text "${missing_row_repo}" '| `support_bundle` | Reviewed bundle identity, environment class, component versions, doctor summary, backup/restore references, upgrade/rollback references, timestamp, owner, and AegisOps evidence links. | Missing provenance, mixed snapshots, or bundle-as-truth claims fail the proof. |'
assert_fails_with "${missing_row_repo}" "Missing Phase 66.6 RC supportability evidence row"

missing_binding_repo="${workdir}/missing-binding"
copy_valid_repo "${missing_binding_repo}"
remove_doc_text "${missing_binding_repo}" 'The `redaction_manifest` value must include `journey_run_id`, `repository_revision`, `manifest_id`, `evidence_reference`, `bundle_reference`, `scan_result=passed`, `secret_values`, `workstation_paths`, `private_payloads`, `ticket_private_content`, `tokens_and_headers`, `certs_and_keys`, `credentials`, `customer_identifiers`, and `authority_boundary=subordinate-evidence-only`.'
assert_fails_with "${missing_binding_repo}" "Missing Phase 66.6 evidence binding statement"

partial_packet_repo="${workdir}/partial-packet"
copy_valid_repo "${partial_packet_repo}"
append_doc_line "${partial_packet_repo}" "journey_run_id=journey-66-1-partial"
assert_fails_with "${partial_packet_repo}" "partial evidence packet"

partial_table_repo="${workdir}/partial-table"
copy_valid_repo "${partial_table_repo}"
printf '\n## Partial Packet\n\n| Field | Value |\n| --- | --- |\n| `journey_run_id` | journey-66-1-partial |\n' >>"${partial_table_repo}/${doc_rel}"
assert_fails_with "${partial_table_repo}" "partial evidence packet"

evidence_section_partial_repo="${workdir}/evidence-section-partial"
copy_valid_repo "${evidence_section_partial_repo}"
insert_before_doc_text \
  "${evidence_section_partial_repo}" \
  "## 3. Evidence Binding And Secret Hygiene" \
  $'| `journey_run_id` | journey-66-1-section-partial |\n'
assert_fails_with "${evidence_section_partial_repo}" "partial evidence packet"

cross_section_union_repo="${workdir}/cross-section-union"
copy_valid_repo "${cross_section_union_repo}"
insert_before_doc_text \
  "${cross_section_union_repo}" \
  "## 3. Evidence Binding And Secret Hygiene" \
  $'| `journey_run_id` | journey-66-1-cross-section |\n'
append_complete_packet "${cross_section_union_repo}"
FIELD="journey_run_id" perl -0pi -e 's/^\Q$ENV{FIELD}\E=.*\n//m' "${cross_section_union_repo}/${doc_rel}"
assert_fails_with "${cross_section_union_repo}" "partial evidence packet"

for field in \
  journey_run_id repository_revision backup_evidence restore_dry_run_evidence upgrade_plan rollback_plan \
  support_bundle redaction_manifest owner_review limitation_references non_claims; do
  missing_field_repo="${workdir}/missing-field-${field}"
  copy_valid_repo "${missing_field_repo}"
  append_complete_packet "${missing_field_repo}"
  FIELD="${field}" perl -0pi -e 's/^\Q$ENV{FIELD}\E=.*\n//m' "${missing_field_repo}/${doc_rel}"
  assert_fails_with "${missing_field_repo}" "partial evidence packet"

  placeholder_field_repo="${workdir}/placeholder-field-${field}"
  copy_valid_repo "${placeholder_field_repo}"
  append_complete_packet "${placeholder_field_repo}"
  FIELD="${field}" perl -0pi -e 's/^\Q$ENV{FIELD}\E=.*$/$ENV{FIELD}=TODO/m' "${placeholder_field_repo}/${doc_rel}"
  assert_fails_with "${placeholder_field_repo}" "invalid ${field}"
done

mismatched_nested_revision_repo="${workdir}/mismatched-nested-revision"
copy_valid_repo "${mismatched_nested_revision_repo}"
append_complete_packet "${mismatched_nested_revision_repo}"
nested_fixture_revision="$(git -C "${mismatched_nested_revision_repo}" rev-parse HEAD)"
replace_doc_text \
  "${mismatched_nested_revision_repo}" \
  "support_bundle" \
  "repository_revision=${nested_fixture_revision}" \
  "repository_revision=ffffffffffffffffffffffffffffffffffffffff"
assert_fails_with "${mismatched_nested_revision_repo}" "repository_revision must match the proof packet"

mixed_revision_repo="${workdir}/mixed-revision"
copy_valid_repo "${mixed_revision_repo}"
append_complete_packet "${mixed_revision_repo}"
printf '%s\n' "repository_revision=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" >>"${mixed_revision_repo}/${doc_rel}"
assert_fails_with "${mixed_revision_repo}" "multiple materialized values"

duplicate_journey_repo="${workdir}/duplicate-journey"
copy_valid_repo "${duplicate_journey_repo}"
append_complete_packet "${duplicate_journey_repo}"
printf '%s\n' "journey_run_id=journey-66-1-duplicate" >>"${duplicate_journey_repo}/${doc_rel}"
assert_fails_with "${duplicate_journey_repo}" "multiple materialized values"

nonexistent_revision_repo="${workdir}/nonexistent-revision"
copy_valid_repo "${nonexistent_revision_repo}"
append_complete_packet "${nonexistent_revision_repo}"
fixture_revision="$(git -C "${nonexistent_revision_repo}" rev-parse HEAD)"
replace_doc_text \
  "${nonexistent_revision_repo}" \
  "repository_revision" \
  "repository_revision=${fixture_revision}" \
  "repository_revision=ffffffffffffffffffffffffffffffffffffffff"
assert_fails_with "${nonexistent_revision_repo}" "does not resolve to a commit"

mutated_packet_case "backup-missing-component" "backup_evidence" "manifest_id=backup-007; custody_reference" "custody_reference" "invalid backup_evidence"
mutated_packet_case "backup-failed" "backup_evidence" "status=completed" "status=failed" "invalid backup_evidence"
mutated_packet_case "backup-broad-owner" "backup_evidence" "owner=group:release-ops" "owner=operator" "accountable person or group"
mutated_packet_case "backup-prefixed-broad-owner" "backup_evidence" "owner=group:release-ops" "owner=group:operators" "accountable person or group"
mutated_packet_case "backup-invalid-time" "backup_evidence" "created_at=${backup_created_at}" "created_at=${decision_date}" "invalid backup_evidence"
mutated_packet_case "restore-before-backup" "restore_dry_run_evidence" "created_at=${restore_created_at}" "created_at=${restore_before_backup}" "restore evidence cannot predate backup evidence"
mutated_packet_case "restore-before-backup-offset" "restore_dry_run_evidence" "created_at=${restore_created_at}" "created_at=${restore_before_backup_offset}" "restore evidence cannot predate backup evidence"
mutated_packet_case "restore-failed" "restore_dry_run_evidence" "result=passed" "result=failed" "invalid restore_dry_run_evidence"
mutated_packet_case "restore-automated-operator" "restore_dry_run_evidence" "operator=group:release-ops" "operator=person:ci-bot" "accountable person or group"
mutated_packet_case "restore-ticket-ref" "restore_dry_run_evidence" "backup_reference=aegisops://evidence/backup-007" "backup_reference=ticket://private/77" "invalid restore_dry_run_evidence"
mutated_packet_case "restore-mismatched-backup" "restore_dry_run_evidence" "backup_reference=aegisops://evidence/backup-007" "backup_reference=aegisops://evidence/backup-008" "backup references must match"
mutated_packet_case "restore-mismatched-profile" "restore_dry_run_evidence" "target_profile=smb-single-node" "target_profile=enterprise-cluster" "target profiles must match"
mutated_packet_case "restore-reuses-backup-reference" "restore_dry_run_evidence" "evidence_reference=aegisops://evidence/restore-dry-007" "evidence_reference=aegisops://evidence/backup-007" "backup and restore evidence references must be distinct"
mutated_packet_case "upgrade-floating-version" "upgrade_plan" "version_after=1.7.0" "version_after=latest" "invalid upgrade_plan"
mutated_packet_case "upgrade-rc-build-version" "upgrade_plan" "version_after=1.7.0" "version_after=1.7.0+rc.1" "invalid upgrade_plan"
mutated_packet_case "upgrade-same-version" "upgrade_plan" "version_after=1.7.0" "version_after=1.6.0" "version_before and version_after must differ"
mutated_packet_case "upgrade-equivalent-v-version" "upgrade_plan" "version_after=1.7.0" "version_after=v1.6.0" "version_before and version_after must differ"
mutated_packet_case "upgrade-failed-preflight" "upgrade_plan" "preflight_result=passed:aegisops://evidence/preflight-007" "preflight_result=failed:aegisops://evidence/preflight-007" "invalid upgrade_plan"
mutated_packet_case "upgrade-smuggled-reference" "upgrade_plan" "evidence_links=aegisops://evidence/upgrade-detail-007" "evidence_links=ticket://private/77?aegisops://evidence/upgrade-detail-007" "invalid upgrade_plan"
mutated_packet_case "rollback-missing-owner" "rollback_plan" "rollback_owner=group:release-ops" "rollback_owner=TODO" "invalid rollback_plan"
mutated_packet_case "rollback-broad-owner" "rollback_plan" "rollback_owner=group:release-ops" "rollback_owner=operator" "accountable person or group"
mutated_packet_case "rollback-vague-trigger" "rollback_plan" "rollback_trigger=failed:aegisops://evidence/post-upgrade-smoke-007" "rollback_trigger=maybe" "actionable failed, rejected, or threshold-breached evidence"
mutated_packet_case "rollback-smuggled-trigger" "rollback_plan" "rollback_trigger=failed:aegisops://evidence/post-upgrade-smoke-007" "rollback_trigger=failed:ticket://private/77?aegisops://evidence/post-upgrade-smoke-007" "actionable failed, rejected, or threshold-breached evidence"
mutated_packet_case "rollback-query-smuggled-trigger" "rollback_plan" "rollback_trigger=failed:aegisops://evidence/post-upgrade-smoke-007" "rollback_trigger=failed:aegisops://evidence/post-upgrade-smoke-007?source=ticket://private/77" "actionable failed, rejected, or threshold-breached evidence"
mutated_packet_case "rollback-ticket-target" "rollback_plan" "rollback_target=aegisops://evidence/backup-007" "rollback_target=ticket://private/77" "invalid rollback_plan"
mutated_packet_case "rollback-mismatched-backup" "rollback_plan" "backup_reference=aegisops://evidence/backup-007" "backup_reference=aegisops://evidence/backup-009" "backup references must match"
mutated_packet_case "rollback-reuses-upgrade-reference" "rollback_plan" "evidence_reference=aegisops://evidence/rollback-007" "evidence_reference=aegisops://evidence/upgrade-007" "upgrade and rollback evidence references must be distinct"
mutated_packet_case "bundle-floating-version" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-latest" "invalid support_bundle"
mutated_packet_case "bundle-list-floating-version" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-latest,wazuh-4.0.0" "invalid support_bundle"
mutated_packet_case "bundle-unversioned-component" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-unversioned,wazuh-4.0.0" "invalid support_bundle"
mutated_packet_case "bundle-version-without-component" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=1.7.0" "invalid support_bundle"
mutated_packet_case "bundle-rc-build-version" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-1.7.0+rc.1" "invalid support_bundle"
mutated_packet_case "bundle-duplicate-component" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-1.7.0,aegisops-v1.7.1" "duplicate component version"
mutated_packet_case "bundle-empty-component" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-1.7.0," "invalid support_bundle"
mutated_packet_case "bundle-before-restore" "support_bundle" "created_at=${bundle_created_at}" "created_at=${bundle_before_restore}" "support bundle cannot predate restore evidence"
mutated_packet_case "bundle-missing-backup-ref" "support_bundle" "backup_restore_references=aegisops://evidence/backup-007,aegisops://evidence/restore-dry-007" "backup_restore_references=aegisops://evidence/restore-dry-007" "backup_restore_references must match"
mutated_packet_case "bundle-missing-restore-ref" "support_bundle" "backup_restore_references=aegisops://evidence/backup-007,aegisops://evidence/restore-dry-007" "backup_restore_references=aegisops://evidence/backup-007" "backup_restore_references must match"
mutated_packet_case "bundle-duplicate-restore-ref" "support_bundle" "backup_restore_references=aegisops://evidence/backup-007,aegisops://evidence/restore-dry-007" "backup_restore_references=aegisops://evidence/backup-007,aegisops://evidence/restore-dry-007,aegisops://evidence/restore-dry-007" "must not contain duplicate evidence references"
mutated_packet_case "bundle-missing-upgrade-ref" "support_bundle" "upgrade_rollback_references=aegisops://evidence/upgrade-007,aegisops://evidence/rollback-007" "upgrade_rollback_references=aegisops://evidence/rollback-007" "upgrade_rollback_references must match"
mutated_packet_case "bundle-missing-rollback-ref" "support_bundle" "upgrade_rollback_references=aegisops://evidence/upgrade-007,aegisops://evidence/rollback-007" "upgrade_rollback_references=aegisops://evidence/upgrade-007" "upgrade_rollback_references must match"
mutated_packet_case "bundle-ticket-links" "support_bundle" "evidence_links=aegisops://evidence/bundle-detail-007" "evidence_links=ticket://private/77" "invalid support_bundle"
mutated_packet_case "redaction-failed" "redaction_manifest" "scan_result=passed" "scan_result=failed" "invalid redaction_manifest"
mutated_packet_case "redaction-retained-secret" "redaction_manifest" "secret_values=absent" "secret_values=retained" "invalid redaction_manifest"
mutated_packet_case "redaction-authority" "redaction_manifest" "authority_boundary=subordinate-evidence-only" "authority_boundary=release-truth" "invalid redaction_manifest"
mutated_packet_case "redaction-mismatched-bundle" "redaction_manifest" "bundle_reference=aegisops://evidence/bundle-007" "bundle_reference=aegisops://evidence/bundle-008" "redaction bundle_reference must match"
mutated_packet_case "redaction-reuses-bundle-reference" "redaction_manifest" "evidence_reference=aegisops://evidence/redaction-007" "evidence_reference=aegisops://evidence/bundle-007" "redaction and support bundle evidence references must be distinct"
mutated_packet_case "artifact-self-review" "owner_review" "reviewer=person:release-owner" "reviewer=verifier-output" "accountable person or group"
mutated_packet_case "automated-self-review" "owner_review" "reviewer=person:release-owner" "reviewer=person:ci-bot" "accountable person or group"
mutated_packet_case "review-missing-redaction" "owner_review" "reviewed_references=aegisops://evidence/bundle-007,aegisops://evidence/redaction-007" "reviewed_references=aegisops://evidence/bundle-007" "reviewed_references must match"
mutated_packet_case "unsupported-review" "owner_review" "disposition=accepted-with-follow-up" "disposition=approved-by-bundle" "invalid owner_review"
mutated_packet_case "review-before-bundle" "owner_review" "reviewed_at=${reviewed_at}" "reviewed_at=${review_before_bundle}" "owner review cannot predate support bundle"

stale_evidence_repo="${workdir}/stale-evidence"
copy_valid_repo "${stale_evidence_repo}"
append_complete_packet "${stale_evidence_repo}"
replace_doc_text "${stale_evidence_repo}" "backup_evidence" "created_at=${backup_created_at}" "created_at=2000-01-01T09:00:00Z"
replace_doc_text "${stale_evidence_repo}" "restore_dry_run_evidence" "created_at=${restore_created_at}" "created_at=2000-01-01T09:15:00Z"
replace_doc_text "${stale_evidence_repo}" "support_bundle" "created_at=${bundle_created_at}" "created_at=2000-01-01T09:30:00Z"
replace_doc_text "${stale_evidence_repo}" "owner_review" "reviewed_at=${reviewed_at}" "reviewed_at=2000-01-01T10:00:00Z"
assert_fails_with "${stale_evidence_repo}" "evidence exceeds the 24-hour freshness window"

mutated_packet_case "future-owner-review" "owner_review" "reviewed_at=${reviewed_at}" "reviewed_at=${future_reviewed_at}" "evidence timestamp is in the future"

mutated_packet_case "invalid-limitation-date" "limitation_references" "decision_date=${decision_date}" "decision_date=21-07-2026" "invalid limitation_references"
mutated_packet_case "impossible-limitation-date" "limitation_references" "decision_date=${decision_date}" "decision_date=2026-13-40" "invalid limitation_references"
mutated_packet_case "limitation-follow-up-before-decision" "limitation_references" "follow_up_date=${follow_up_date}" "follow_up_date=${prior_date}" "follow_up_date cannot predate decision_date"
mutated_packet_case "embedded-owner-placeholder" "owner_review" "follow_up_owner=group:support-owner" "follow_up_owner=group:support-TODO" "invalid owner_review"
mutated_packet_case "missing-non-claim" "non_claims" "not-customer-portal," "" "invalid non_claims"

for field in \
  backup_evidence restore_dry_run_evidence upgrade_plan rollback_plan support_bundle \
  redaction_manifest owner_review limitation_references; do
  mutated_packet_case \
    "mismatched-journey-${field}" \
    "${field}" \
    "journey_run_id=journey-66-1-0007" \
    "journey_run_id=journey-66-1-other" \
    "journey_run_id must match the proof packet"
  mutated_packet_case \
    "missing-journey-${field}" \
    "${field}" \
    "journey_run_id=journey-66-1-0007; " \
    "" \
    "missing components journey_run_id"
done

stable_build_metadata_repo="${workdir}/stable-build-metadata"
copy_valid_repo "${stable_build_metadata_repo}"
append_complete_packet "${stable_build_metadata_repo}"
replace_doc_text "${stable_build_metadata_repo}" "upgrade_plan" "version_after=1.7.0" "version_after=1.7.0+build.7"
replace_doc_text "${stable_build_metadata_repo}" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-1.7.0+build.7,wazuh-v4.0.0"
assert_passes "${stable_build_metadata_repo}"

forbidden_claim_case "bundle-rc-overclaim" "Support bundle proves RC gate readiness."
forbidden_claim_case "bundle-is-readiness-proof" "Support bundle is a GA readiness proof."
forbidden_claim_case "bundle-provides-readiness" "Support bundle provides GA readiness."
forbidden_claim_case "bundle-constitutes-readiness" "Support bundle constitutes GA readiness."
forbidden_claim_case "bundle-delivers-readiness" "Support bundle delivers GA readiness."
forbidden_claim_case "article-bundle-offers-readiness" "The support bundle offers GA readiness."
forbidden_claim_case "source-led-readiness" "According to the support bundle, GA readiness is established."
forbidden_claim_case "unrelated-negation-readiness" "Support bundle does not include diagnostics, provides GA readiness."
forbidden_claim_case "earlier-negated-later-positive-readiness" "Support bundle cannot prove RC readiness, provides GA readiness."
forbidden_claim_case "reverse-readiness-source" "GA readiness comes from the support bundle."
forbidden_claim_case "phase-provides-readiness" "Phase 66.6 provides GA readiness."
forbidden_claim_case "phase-delivers-readiness" "Phase 66.6 delivers GA readiness."
forbidden_claim_case "phase-serves-as-readiness" "Phase 66.6 serves as GA readiness proof."
forbidden_claim_case "bundle-truth" "Support bundle is release truth."
forbidden_claim_case "bundle-release-gate" "Support bundle is the release gate."
forbidden_claim_case "bundle-serves-as-release-gate" "Support bundle serves as a release gate."
forbidden_claim_case "bundle-acts-as-release-gate" "Support bundle acts as a release gate."
forbidden_claim_case "reverse-release-gate" "The release gate is the support bundle."
forbidden_claim_case "dry-run-authority" "Restore dry-run output approves AegisOps records."
forbidden_claim_case "proof-ga-overclaim" "This proof demonstrates GA readiness."
forbidden_claim_case "verifier-ga-overclaim" "Verifier output validates GA readiness."
forbidden_claim_case "passive-ga-overclaim" "GA readiness is proven by the support bundle."
forbidden_claim_case "passive-restore-overclaim" "Live restore completion is confirmed by restore dry-run output."
forbidden_claim_case "support-operator-authority" "Support collaborator can approve actions."
forbidden_claim_case "adversative-overclaim" "Support bundle cannot prove RC readiness but proves GA readiness."
forbidden_claim_case "unrelated-without-overclaim" "Support bundle proves GA readiness without a manual review."
forbidden_claim_case "pre-predicate-without-overclaim" "Support bundle without a manual review proves GA readiness."
forbidden_claim_case "passive-interposed-without-overclaim" "GA readiness is proven without operator review by the support bundle."
forbidden_claim_case "comment-overclaim" "<!-- Support bundle proves RC gate readiness. -->"

readme_overclaim_repo="${workdir}/readme-overclaim"
copy_valid_repo "${readme_overclaim_repo}"
printf '%s\n' "Phase 66.6 supportability proof proves GA readiness." >>"${readme_overclaim_repo}/README.md"
assert_fails_with "${readme_overclaim_repo}" "authority or readiness overclaim detected"

safe_non_claim_repo="${workdir}/safe-non-claim"
copy_valid_repo "${safe_non_claim_repo}"
append_doc_line "${safe_non_claim_repo}" "Support bundle cannot prove RC gate readiness."
append_doc_line "${safe_non_claim_repo}" "GA readiness is not proven by the support bundle."
append_doc_line "${safe_non_claim_repo}" "This proof does not establish commercial replacement readiness."
append_doc_line "${safe_non_claim_repo}" "Restore dry-run output never proves live restore completion."
append_doc_line "${safe_non_claim_repo}" "Support bundle does not prove GA readiness without manual review."
append_doc_line "${safe_non_claim_repo}" "Support bundle may not prove GA readiness."
append_doc_line "${safe_non_claim_repo}" "Support bundle is not a GA readiness proof."
append_doc_line "${safe_non_claim_repo}" "Support bundle does not provide GA readiness."
append_doc_line "${safe_non_claim_repo}" "The support bundle does not provide GA readiness."
append_doc_line "${safe_non_claim_repo}" "GA readiness does not come from the support bundle."
append_doc_line "${safe_non_claim_repo}" "This proof must reject GA readiness claims."
append_doc_line "${safe_non_claim_repo}" "This proof excludes commercial replacement claims."
append_doc_line "${safe_non_claim_repo}" "Support bundle is no proof of GA readiness."
append_doc_line "${safe_non_claim_repo}" "Support bundle lacks proof of GA readiness."
append_doc_line "${safe_non_claim_repo}" "Support bundle operates without proving GA readiness."
append_doc_line "${safe_non_claim_repo}" "Phase 66.6 does not provide GA readiness."
append_doc_line "${safe_non_claim_repo}" "Support bundle is not the release gate."
append_doc_line "${safe_non_claim_repo}" "Support bundle cannot serve as a release gate."
assert_passes "${safe_non_claim_repo}"

leak_case "password-leak" "support_password=SuperSecretValue123" "production secret-looking value detected"
leak_case "redaction-prefix-password-leak" "password=[REDACTED:secret]SuperSecretValue123" "production secret-looking value detected"
leak_case "quoted-redaction-prefix-password-leak" 'password="[REDACTED:secret]SuperSecretValue123"' "production secret-looking value detected"
leak_case "short-redaction-prefix-password-leak" "password=[REDACTED]SuperSecretValue123" "production secret-looking value detected"
leak_case "whitespace-redaction-password-leak" "password=[REDACTED] SuperSecretValue123" "production secret-looking value detected"
leak_case "tab-redaction-password-leak" $'password=[REDACTED:secret]\tSuperSecretValue123' "production secret-looking value detected"
leak_case "quoted-whitespace-redaction-password-leak" 'password="[REDACTED:secret]" SuperSecretValue123' "production secret-looking value detected"
leak_case "bearer-leak" "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456" "production secret-looking value detected"
leak_case "equals-bearer-leak" "Authorization=Bearer abcdefghijklmnopqrstuvwxyz123456" "production secret-looking value detected"
leak_case "cookie-leak" "Cookie: session=abcdefghijklmnopqrstuvwx" "production secret-looking value detected"
leak_case "set-cookie-leak" "Set-Cookie: session=abcdefghijklmnopqrstuvwx; Secure" "production secret-looking value detected"
leak_case "forwarded-header-leak" "X-Forwarded-For: 192.0.2.10" "production secret-looking value detected"
leak_case "tenant-header-leak" "X-Tenant-ID: tenant-acme-001" "production secret-looking value detected"
leak_case "proxy-authorization-leak" "Proxy-Authorization: Basic abcdefghijklmnopqrstuvwx" "production secret-looking value detected"
leak_case "rfc-forwarded-header-leak" "Forwarded: for=192.0.2.10;proto=https" "production secret-looking value detected"
leak_case "host-header-leak" "Host: customer.internal" "production secret-looking value detected"
leak_case "jwt-leak" "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdXBwb3J0In0.signaturevalue123" "production secret-looking value detected"
leak_case "api-key-leak" "api_key=abcdefghijklmnop1234567890" "production secret-looking value detected"
leak_case "generic-token-leak" "token=SuperSecretValue123" "production secret-looking value detected"
leak_case "prefixed-token-leak" "support_token=SuperSecretValue123" "production secret-looking value detected"
leak_case "private-key-leak" "-----BEGIN PRIVATE KEY-----" "production secret-looking value detected"
leak_case "certificate-leak" "-----BEGIN CERTIFICATE-----" "production secret-looking value detected"
leak_case "trusted-certificate-leak" "-----BEGIN TRUSTED CERTIFICATE-----" "production secret-looking value detected"
leak_case "x509-certificate-leak" "-----BEGIN X509 CERTIFICATE-----" "production secret-looking value detected"
leak_case "certificate-request-leak" "-----BEGIN CERTIFICATE REQUEST-----" "production secret-looking value detected"
leak_case "new-certificate-request-leak" "-----BEGIN NEW CERTIFICATE REQUEST-----" "production secret-looking value detected"
leak_case "credential-url-leak" "postgres://support:credentialvalue123@db.internal/aegisops" "production secret-looking value detected"
leak_case "comment-secret-leak" "<!-- password=CommentSecretValue123 -->" "production secret-looking value detected"

safe_redaction_repo="${workdir}/safe-redaction-marker"
copy_valid_repo "${safe_redaction_repo}"
append_doc_line "${safe_redaction_repo}" "password=[REDACTED:secret]"
append_doc_line "${safe_redaction_repo}" "client_secret=[REDACTED]."
append_doc_line "${safe_redaction_repo}" 'api_key="[REDACTED:secret]"'
append_doc_line "${safe_redaction_repo}" "access_token=[REDACTED:token]   "
append_doc_line "${safe_redaction_repo}" "token=[REDACTED:token]"
append_doc_line "${safe_redaction_repo}" "Authorization=[REDACTED:authorization]"
append_doc_line "${safe_redaction_repo}" "Cookie: [REDACTED:cookie]"
assert_passes "${safe_redaction_repo}"

leak_case "customer-private-leak" "The bundle contains raw customer payload data." "customer-private or ticket-private data detected"
leak_case "private-ticket-leak" "The bundle retains private ticket content." "customer-private or ticket-private data detected"
leak_case "customer-assignment-leak" "customer_private_data=Acme raw incident payload" "customer-private or ticket-private data detected"
leak_case "customer-email-leak" "customer_email=alice@example.com" "customer-private or ticket-private data detected"
leak_case "tenant-id-leak" "tenant_id=tenant-acme-001" "customer-private or ticket-private data detected"
leak_case "customer-account-name-leak" "customer_account_name=Acme" "customer-private or ticket-private data detected"
leak_case "account-name-leak" "account_name=Acme" "customer-private or ticket-private data detected"
leak_case "bare-email-leak" "Contact alice@example.com for the retained case." "customer-private or ticket-private data detected"
leak_case "comment-tenant-id-leak" "<!-- tenant_id=tenant-acme-001 -->" "customer-private or ticket-private data detected"
leak_case "customer-name-prose-leak" "Customer Acme is included in the bundle." "customer-private or ticket-private data detected"
leak_case "customer-name-object-leak" "The bundle includes customer Acme." "customer-private or ticket-private data detected"
leak_case "tenant-name-prose-leak" 'Tenant "Acme Corp" is retained in the bundle.' "customer-private or ticket-private data detected"
leak_case "customer-key-leak" "customer=Acme" "customer-private or ticket-private data detected"
leak_case "customer-copular-leak" "The customer is Acme." "customer-private or ticket-private data detected"
leak_case "reverse-customer-copular-leak" "Acme is the retained customer." "customer-private or ticket-private data detected"
leak_case "comment-private-leak" "<!-- The bundle exports customer-private logs. -->" "customer-private or ticket-private data detected"
leak_case "unrelated-private-negation" "The bundle must not contain diagnostics, but it retains private ticket content." "customer-private or ticket-private data detected"

safe_redaction_repo="${workdir}/safe-redaction"
copy_valid_repo "${safe_redaction_repo}"
append_doc_line "${safe_redaction_repo}" "The bundle must not contain raw customer payloads and rejects private ticket content."
append_doc_line "${safe_redaction_repo}" "Customer-private data is redacted before retention."
append_doc_line "${safe_redaction_repo}" "The bundle does not retain private ticket content."
append_doc_line "${safe_redaction_repo}" "The bundle retains no private ticket content."
append_doc_line "${safe_redaction_repo}" "customer_email=[REDACTED:customer-identifier]"
append_doc_line "${safe_redaction_repo}" "tenant_id=redacted"
append_doc_line "${safe_redaction_repo}" "customer_account_name=removed"
append_doc_line "${safe_redaction_repo}" "account_name=absent"
append_doc_line "${safe_redaction_repo}" "Customer identifiers are redacted before retention."
append_doc_line "${safe_redaction_repo}" "The bundle does not include customer Acme."
append_doc_line "${safe_redaction_repo}" "Customer Support is included only as a generic capability label."
append_doc_line "${safe_redaction_repo}" "customer=[REDACTED:customer-identifier]"
assert_passes "${safe_redaction_repo}"

macos_path_fragment="/""Users/example"
linux_path_fragment="/""home/example"
windows_path_fragment="C:""\\Users\\example"
tilde_home_fragment="~""/.ssh"
root_home_fragment="/""root"
leak_case "macos-path-leak" "Retain ${macos_path_fragment}/bundle.log." "workstation-local path detected"
leak_case "linux-path-leak" "Retain ${linux_path_fragment}/bundle.log." "workstation-local path detected"
leak_case "windows-path-leak" "Retain ${windows_path_fragment}\\bundle.log." "workstation-local path detected"
leak_case "file-uri-path-leak" "Retain file://${linux_path_fragment}/bundle.log." "workstation-local path detected"
leak_case "comment-path-leak" "<!-- Retain ${macos_path_fragment}/bundle.log. -->" "workstation-local path detected"
leak_case "tilde-home-path-leak" "Retain ${tilde_home_fragment}/id_ed25519." "workstation-local path detected"
leak_case "root-home-path-leak" "Retain ${root_home_fragment}/.config/aegisops/bundle.log." "workstation-local path detected"
leak_case "root-file-uri-path-leak" "Retain file://${root_home_fragment}/.config/aegisops/bundle.log." "workstation-local path detected"

external_url_repo="${workdir}/external-url"
copy_valid_repo "${external_url_repo}"
append_doc_line "${external_url_repo}" "Use https://example.com/home/docs/supportability.html as public reference context."
append_doc_line "${external_url_repo}" 'Use ${HOME}/.config/aegisops as a documented environment-relative placeholder.'
assert_passes "${external_url_repo}"

path_hygiene_repo="${workdir}/path-hygiene"
copy_valid_repo "${path_hygiene_repo}"
printf '%s\n' "Retain ${macos_path_fragment}/outside-proof.log." >"${path_hygiene_repo}/docs/path-hygiene-fixture.md"
git -C "${path_hygiene_repo}" add docs/path-hygiene-fixture.md
assert_fails_with_path_hygiene "${path_hygiene_repo}" "publishable path hygiene failed"

echo "Phase 66.6 RC supportability verifier rejects partial packets, malformed evidence, secrets, private data, paths, authority expansion, and readiness overclaims."
