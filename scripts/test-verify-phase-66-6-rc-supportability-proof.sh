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

packet_lines=(
  "journey_run_id=journey-66-1-0007"
  "repository_revision=__REPOSITORY_REVISION__"
  "backup_evidence=manifest_id=backup-007; custody_reference=aegisops://evidence/backup-007; created_at=2026-07-21T09:00:00Z; owner=release-ops; status=completed"
  "restore_dry_run_evidence=dry_run_id=restore-dry-007; backup_reference=aegisops://evidence/backup-007; target_profile=smb-single-node; created_at=2026-07-21T09:15:00Z; operator=release-ops; result=passed"
  "upgrade_plan=plan_id=upgrade-007; version_before=1.6.0; version_after=1.7.0; target_profile=smb-single-node; preflight_result=passed:aegisops://evidence/preflight-007; evidence_links=aegisops://evidence/upgrade-007"
  "rollback_plan=plan_id=rollback-007; backup_reference=aegisops://evidence/backup-007; rollback_owner=release-ops; rollback_trigger=post-upgrade-smoke-failure; rollback_target=aegisops://evidence/backup-007"
  "support_bundle=bundle_id=bundle-007; environment_class=rc-lab; component_versions=aegisops-1.7.0; doctor_summary=aegisops://evidence/doctor-007; backup_restore_references=aegisops://evidence/recovery-007; upgrade_rollback_references=aegisops://evidence/change-007; created_at=2026-07-21T09:30:00Z; owner=support-review; evidence_links=aegisops://evidence/bundle-007"
  "redaction_manifest=manifest_id=redaction-007; scan_result=passed; secret_values=absent; workstation_paths=absent; private_payloads=redacted; ticket_private_content=absent; tokens_and_headers=absent; certs_and_keys=absent; credentials=absent; customer_identifiers=redacted; authority_boundary=subordinate-evidence-only"
  "owner_review=reviewer=release-owner; reviewed_at=2026-07-21T10:00:00Z; disposition=accepted-with-follow-up; accepted_risk=bounded-rc-only; follow_up_owner=support-owner"
  "limitation_references=ids=LIM-66-006; owner=support-owner; decision_date=2026-07-21; follow_up_date=2026-08-15"
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
remove_doc_text "${missing_binding_repo}" 'The `redaction_manifest` value must include `manifest_id`, `scan_result=passed`, `secret_values`, `workstation_paths`, `private_payloads`, `ticket_private_content`, `tokens_and_headers`, `certs_and_keys`, `credentials`, `customer_identifiers`, and `authority_boundary=subordinate-evidence-only`.'
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
mutated_packet_case "backup-invalid-time" "backup_evidence" "created_at=2026-07-21T09:00:00Z" "created_at=2026-07-21" "invalid backup_evidence"
mutated_packet_case "restore-failed" "restore_dry_run_evidence" "result=passed" "result=failed" "invalid restore_dry_run_evidence"
mutated_packet_case "restore-ticket-ref" "restore_dry_run_evidence" "backup_reference=aegisops://evidence/backup-007" "backup_reference=ticket://private/77" "invalid restore_dry_run_evidence"
mutated_packet_case "restore-mismatched-backup" "restore_dry_run_evidence" "backup_reference=aegisops://evidence/backup-007" "backup_reference=aegisops://evidence/backup-008" "backup references must match"
mutated_packet_case "restore-mismatched-profile" "restore_dry_run_evidence" "target_profile=smb-single-node" "target_profile=enterprise-cluster" "target profiles must match"
mutated_packet_case "upgrade-floating-version" "upgrade_plan" "version_after=1.7.0" "version_after=latest" "invalid upgrade_plan"
mutated_packet_case "upgrade-same-version" "upgrade_plan" "version_after=1.7.0" "version_after=1.6.0" "version_before and version_after must differ"
mutated_packet_case "upgrade-equivalent-v-version" "upgrade_plan" "version_after=1.7.0" "version_after=v1.6.0" "version_before and version_after must differ"
mutated_packet_case "upgrade-failed-preflight" "upgrade_plan" "preflight_result=passed:aegisops://evidence/preflight-007" "preflight_result=failed:aegisops://evidence/preflight-007" "invalid upgrade_plan"
mutated_packet_case "upgrade-smuggled-reference" "upgrade_plan" "evidence_links=aegisops://evidence/upgrade-007" "evidence_links=ticket://private/77?aegisops://evidence/upgrade-007" "invalid upgrade_plan"
mutated_packet_case "rollback-missing-owner" "rollback_plan" "rollback_owner=release-ops" "rollback_owner=TODO" "invalid rollback_plan"
mutated_packet_case "rollback-ticket-target" "rollback_plan" "rollback_target=aegisops://evidence/backup-007" "rollback_target=ticket://private/77" "invalid rollback_plan"
mutated_packet_case "rollback-mismatched-backup" "rollback_plan" "backup_reference=aegisops://evidence/backup-007" "backup_reference=aegisops://evidence/backup-009" "backup references must match"
mutated_packet_case "bundle-floating-version" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-latest" "invalid support_bundle"
mutated_packet_case "bundle-list-floating-version" "support_bundle" "component_versions=aegisops-1.7.0" "component_versions=aegisops-latest,wazuh-4.0.0" "invalid support_bundle"
mutated_packet_case "bundle-ticket-links" "support_bundle" "evidence_links=aegisops://evidence/bundle-007" "evidence_links=ticket://private/77" "invalid support_bundle"
mutated_packet_case "redaction-failed" "redaction_manifest" "scan_result=passed" "scan_result=failed" "invalid redaction_manifest"
mutated_packet_case "redaction-retained-secret" "redaction_manifest" "secret_values=absent" "secret_values=retained" "invalid redaction_manifest"
mutated_packet_case "redaction-authority" "redaction_manifest" "authority_boundary=subordinate-evidence-only" "authority_boundary=release-truth" "invalid redaction_manifest"
mutated_packet_case "artifact-self-review" "owner_review" "reviewer=release-owner" "reviewer=verifier-output" "invalid owner_review"
mutated_packet_case "unsupported-review" "owner_review" "disposition=accepted-with-follow-up" "disposition=approved-by-bundle" "invalid owner_review"
mutated_packet_case "invalid-limitation-date" "limitation_references" "decision_date=2026-07-21" "decision_date=21-07-2026" "invalid limitation_references"
mutated_packet_case "impossible-limitation-date" "limitation_references" "decision_date=2026-07-21" "decision_date=2026-13-40" "invalid limitation_references"
mutated_packet_case "embedded-owner-placeholder" "owner_review" "follow_up_owner=support-owner" "follow_up_owner=support-TODO" "invalid owner_review"
mutated_packet_case "missing-non-claim" "non_claims" "not-customer-portal," "" "invalid non_claims"

forbidden_claim_case "bundle-rc-overclaim" "Support bundle proves RC gate readiness."
forbidden_claim_case "bundle-truth" "Support bundle is release truth."
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
assert_passes "${safe_non_claim_repo}"

leak_case "password-leak" "support_password=SuperSecretValue123" "production secret-looking value detected"
leak_case "bearer-leak" "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456" "production secret-looking value detected"
leak_case "jwt-leak" "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdXBwb3J0In0.signaturevalue123" "production secret-looking value detected"
leak_case "api-key-leak" "api_key=abcdefghijklmnop1234567890" "production secret-looking value detected"
leak_case "private-key-leak" "-----BEGIN PRIVATE KEY-----" "production secret-looking value detected"
leak_case "certificate-leak" "-----BEGIN CERTIFICATE-----" "production secret-looking value detected"
leak_case "credential-url-leak" "postgres://support:credentialvalue123@db.internal/aegisops" "production secret-looking value detected"
leak_case "comment-secret-leak" "<!-- password=CommentSecretValue123 -->" "production secret-looking value detected"

leak_case "customer-private-leak" "The bundle contains raw customer payload data." "customer-private or ticket-private data detected"
leak_case "private-ticket-leak" "The bundle retains private ticket content." "customer-private or ticket-private data detected"
leak_case "customer-assignment-leak" "customer_private_data=Acme raw incident payload" "customer-private or ticket-private data detected"
leak_case "comment-private-leak" "<!-- The bundle exports customer-private logs. -->" "customer-private or ticket-private data detected"
leak_case "unrelated-private-negation" "The bundle must not contain diagnostics, but it retains private ticket content." "customer-private or ticket-private data detected"

safe_redaction_repo="${workdir}/safe-redaction"
copy_valid_repo "${safe_redaction_repo}"
append_doc_line "${safe_redaction_repo}" "The bundle must not contain raw customer payloads and rejects private ticket content."
append_doc_line "${safe_redaction_repo}" "Customer-private data is redacted before retention."
append_doc_line "${safe_redaction_repo}" "The bundle does not retain private ticket content."
append_doc_line "${safe_redaction_repo}" "The bundle retains no private ticket content."
assert_passes "${safe_redaction_repo}"

macos_path_fragment="/""Users/example"
linux_path_fragment="/""home/example"
windows_path_fragment="C:""\\Users\\example"
leak_case "macos-path-leak" "Retain ${macos_path_fragment}/bundle.log." "workstation-local path detected"
leak_case "linux-path-leak" "Retain ${linux_path_fragment}/bundle.log." "workstation-local path detected"
leak_case "windows-path-leak" "Retain ${windows_path_fragment}\\bundle.log." "workstation-local path detected"
leak_case "file-uri-path-leak" "Retain file://${linux_path_fragment}/bundle.log." "workstation-local path detected"
leak_case "comment-path-leak" "<!-- Retain ${macos_path_fragment}/bundle.log. -->" "workstation-local path detected"

external_url_repo="${workdir}/external-url"
copy_valid_repo "${external_url_repo}"
append_doc_line "${external_url_repo}" "Use https://example.com/home/docs/supportability.html as public reference context."
assert_passes "${external_url_repo}"

path_hygiene_repo="${workdir}/path-hygiene"
copy_valid_repo "${path_hygiene_repo}"
printf '%s\n' "Retain ${macos_path_fragment}/outside-proof.log." >"${path_hygiene_repo}/docs/path-hygiene-fixture.md"
git -C "${path_hygiene_repo}" add docs/path-hygiene-fixture.md
assert_fails_with_path_hygiene "${path_hygiene_repo}" "publishable path hygiene failed"

echo "Phase 66.6 RC supportability verifier rejects partial packets, malformed evidence, secrets, private data, paths, authority expansion, and readiness overclaims."
