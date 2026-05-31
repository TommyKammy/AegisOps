#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-64-5-phase66-limitation-handoff.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

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

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/README.md" "${target}/README.md"
  cp "${repo_root}/docs/phase-64-5-phase66-limitation-handoff.md" "${target}/docs/phase-64-5-phase66-limitation-handoff.md"
  cp "${repo_root}/docs/phase-64-1-known-limitation-ownership-record-contract.md" "${target}/docs/phase-64-1-known-limitation-ownership-record-contract.md"
  cp "${repo_root}/docs/phase-64-1-reviewed-limitation-ownership-records.md" "${target}/docs/phase-64-1-reviewed-limitation-ownership-records.md"
  cp "${repo_root}/docs/phase-63-closeout-evaluation.md" "${target}/docs/phase-63-closeout-evaluation.md"
  cp "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "${target}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-64-5-phase66-limitation-handoff.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
cp "${repo_root}/docs/phase-64-1-known-limitation-ownership-record-contract.md" "${missing_doc_repo}/docs/phase-64-1-known-limitation-ownership-record-contract.md"
cp "${repo_root}/docs/phase-64-1-reviewed-limitation-ownership-records.md" "${missing_doc_repo}/docs/phase-64-1-reviewed-limitation-ownership-records.md"
cp "${repo_root}/docs/phase-63-closeout-evaluation.md" "${missing_doc_repo}/docs/phase-63-closeout-evaluation.md"
cp "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" "${missing_doc_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 64.5 Phase 66 limitation handoff evidence: docs/phase-64-5-phase66-limitation-handoff.md"

missing_readme_bullet_repo="${workdir}/missing-readme-bullet"
copy_valid_repo "${missing_readme_bullet_repo}"
perl -0pi -e 's/- \[Phase 64\.5 Phase 66 limitation handoff\]\(docs\/phase-64-5-phase66-limitation-handoff\.md\)[^\n]*\n//' \
  "${missing_readme_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet"

missing_owner_repo="${workdir}/missing-owner"
copy_valid_repo "${missing_owner_repo}"
remove_doc_text "${missing_owner_repo}" "Every Phase 66 limitation handoff entry requires limitation id, owner, mitigation status, evidence references, open blockers, accepted risks, next review date, and RC-gate consumption notes."
assert_fails_with \
  "${missing_owner_repo}" \
  "Missing required Phase 64.5 handoff term in docs/phase-64-5-phase66-limitation-handoff.md: Every Phase 66 limitation handoff entry requires limitation id, owner"

missing_open_blocker_repo="${workdir}/missing-open-blocker"
copy_valid_repo "${missing_open_blocker_repo}"
remove_doc_text "${missing_open_blocker_repo}" "Every Phase 66 limitation handoff entry requires limitation id, owner, mitigation status, evidence references, open blockers, accepted risks, next review date, and RC-gate consumption notes."
assert_fails_with \
  "${missing_open_blocker_repo}" \
  "Missing required Phase 64.5 handoff term in docs/phase-64-5-phase66-limitation-handoff.md: Every Phase 66 limitation handoff entry requires"

missing_next_review_repo="${workdir}/missing-next-review"
copy_valid_repo "${missing_next_review_repo}"
remove_doc_text "${missing_next_review_repo}" "Every Phase 66 limitation handoff entry requires limitation id, owner, mitigation status, evidence references, open blockers, accepted risks, next review date, and RC-gate consumption notes."
assert_fails_with \
  "${missing_next_review_repo}" \
  "Missing required Phase 64.5 handoff term in docs/phase-64-5-phase66-limitation-handoff.md: Every Phase 66 limitation handoff entry requires"

stale_next_review_repo="${workdir}/stale-next-review"
copy_valid_repo "${stale_next_review_repo}"
perl -0pi -e 's/2026-06-15/2020-01-01/g' \
  "${stale_next_review_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${stale_next_review_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: next review date must be after the handoff document date"

invalid_next_review_repo="${workdir}/invalid-next-review"
copy_valid_repo "${invalid_next_review_repo}"
perl -0pi -e 's/2026-06-15/2026-13-40/g' \
  "${invalid_next_review_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${invalid_next_review_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: next review date must use a real YYYY-MM-DD calendar date"

missing_subordinate_repo="${workdir}/missing-subordinate"
copy_valid_repo "${missing_subordinate_repo}"
remove_doc_text "${missing_subordinate_repo}" 'The handoff references reviewed Phase 64 known limitation ownership records in `docs/phase-64-1-reviewed-limitation-ownership-records.md` as subordinate evidence only.'
assert_fails_with \
  "${missing_subordinate_repo}" \
  "Missing required Phase 64.5 handoff term in docs/phase-64-5-phase66-limitation-handoff.md: The handoff references reviewed Phase 64 known limitation ownership records"

missing_reviewed_record_reference_repo="${workdir}/missing-reviewed-record-reference"
copy_valid_repo "${missing_reviewed_record_reference_repo}"
remove_doc_text "${missing_reviewed_record_reference_repo}" '`docs/phase-64-1-reviewed-limitation-ownership-records.md#limitation-phase64-rc-gate-consumption-001`; '
assert_fails_with \
  "${missing_reviewed_record_reference_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-rc-gate-consumption-001: missing reviewed Phase 64 limitation record reference"

missing_reviewed_evidence_reference_repo="${workdir}/missing-reviewed-evidence-reference"
copy_valid_repo "${missing_reviewed_evidence_reference_repo}"
remove_doc_text "${missing_reviewed_evidence_reference_repo}" '`docs/phase-63-closeout-evaluation.md#support-bundle-gap-disposition`; '
assert_fails_with \
  "${missing_reviewed_evidence_reference_repo}" \
  'Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: missing reviewed Phase 64 evidence reference `docs/phase-63-closeout-evaluation.md#support-bundle-gap-disposition`'

missing_reviewed_record_repo="${workdir}/missing-reviewed-record"
copy_valid_repo "${missing_reviewed_record_repo}"
perl -0pi -e 's/\| `limitation-phase64-rc-gate-consumption-001`[^\n]*\n//' \
  "${missing_reviewed_record_repo}/docs/phase-64-1-reviewed-limitation-ownership-records.md"
assert_fails_with \
  "${missing_reviewed_record_repo}" \
  "Missing required Phase 64.1 reviewed limitation record term"

duplicate_reviewed_record_repo="${workdir}/duplicate-reviewed-record"
copy_valid_repo "${duplicate_reviewed_record_repo}"
printf '%s\n' '| `limitation-phase64-support-bundle-001` | Duplicate support bundle evidence. | material | supportability_evidence | duplicate-owner | Contradict the reviewed support bundle slice. | `docs/phase-63-closeout-evaluation.md#support-bundle-gap-disposition` | mitigation_planned | weekly | none | duplicate_posture | handoff_required | reviewed_evidence_input_only |' \
  >>"${duplicate_reviewed_record_repo}/docs/phase-64-1-reviewed-limitation-ownership-records.md"
assert_fails_with \
  "${duplicate_reviewed_record_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: duplicate reviewed Phase 64 limitation records"

duplicate_handoff_row_repo="${workdir}/duplicate-handoff-row"
copy_valid_repo "${duplicate_handoff_row_repo}"
perl -0pi -e 's/(\| `limitation-phase64-support-bundle-001`[^\n]*\n)/$1$1/' \
  "${duplicate_handoff_row_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${duplicate_handoff_row_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: duplicate Phase 64.5 handoff rows"

missing_row_blocker_repo="${workdir}/missing-row-blocker"
copy_valid_repo "${missing_row_blocker_repo}"
remove_doc_text "${missing_row_blocker_repo}" "RC gate packet must still prove install, Wazuh signal, Shuffle execution, AI trace, report export, restore dry-run, upgrade plan, support bundle, and limitations ownership evidence against the approved RC gate."
assert_fails_with \
  "${missing_row_blocker_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-rc-gate-consumption-001: missing open blockers"

punctuated_placeholder_blocker_repo="${workdir}/punctuated-placeholder-blocker"
copy_valid_repo "${punctuated_placeholder_blocker_repo}"
perl -0pi -e 's/Phase 51\.3 support bundle command, redaction review, included record identifiers, omitted private data classes, owner, retention expectation, and verifier evidence remain required before RC proof can treat support evidence as satisfied\./TBD./' \
  "${punctuated_placeholder_blocker_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${punctuated_placeholder_blocker_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: missing open blockers"

malformed_extra_row_repo="${workdir}/malformed-extra-row"
copy_valid_repo "${malformed_extra_row_repo}"
perl -0pi -e 's/\| `limitation-phase64-support-bundle-001`/\|`limitation-phase64-extra-002`\| \| \| \| \| \| \| \|\n| `limitation-phase64-support-bundle-001`/' \
  "${malformed_extra_row_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${malformed_extra_row_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-extra-002: missing owner"

missing_required_handoff_row_repo="${workdir}/missing-required-handoff-row"
copy_valid_repo "${missing_required_handoff_row_repo}"
perl -0pi -e 's/\| `limitation-phase64-rc-gate-consumption-001`[^\n]*\n//' \
  "${missing_required_handoff_row_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${missing_required_handoff_row_repo}" \
  "Missing Phase 64.5 handoff row for reviewed Phase 64 limitation: limitation-phase64-rc-gate-consumption-001"

wrong_owner_repo="${workdir}/wrong-owner"
copy_valid_repo "${wrong_owner_repo}"
perl -0pi -e 's/supportability-owner/wrong-owner/' \
  "${wrong_owner_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${wrong_owner_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: owner does not match reviewed Phase 64 record"

wrong_mitigation_status_repo="${workdir}/wrong-mitigation-status"
copy_valid_repo "${wrong_mitigation_status_repo}"
perl -0pi -e 's/accepted risk; support bundle evidence remains separately tracked/mitigation planned; support bundle evidence remains separately tracked/' \
  "${wrong_mitigation_status_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${wrong_mitigation_status_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: mitigation status does not match reviewed Phase 64 record"

negated_mitigation_status_repo="${workdir}/negated-mitigation-status"
copy_valid_repo "${negated_mitigation_status_repo}"
perl -0pi -e 's/accepted risk; support bundle evidence remains separately tracked/not accepted risk; support bundle evidence remains separately tracked/' \
  "${negated_mitigation_status_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${negated_mitigation_status_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: mitigation status does not match reviewed Phase 64 record"

wrong_accepted_risk_repo="${workdir}/wrong-accepted-risk"
copy_valid_repo "${wrong_accepted_risk_repo}"
perl -0pi -e 's/bounded pre-RC limitation; accepted only as reviewed ownership evidence/wrong accepted risk posture/' \
  "${wrong_accepted_risk_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${wrong_accepted_risk_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-support-bundle-001: accepted risks does not match reviewed Phase 64 record"

missing_remaining_obligations_repo="${workdir}/missing-remaining-obligations"
copy_valid_repo "${missing_remaining_obligations_repo}"
remove_doc_text "${missing_remaining_obligations_repo}" "Remaining Phase 66 proof obligations: independent RC gate packet, support bundle evidence, restore evidence, upgrade and rollback evidence, first-user RC behavior, daily-operator RC behavior, supportability evidence, security review, packaging evidence, issue-lint evidence, verifier evidence, and explicit gate acceptance outside this handoff."
assert_fails_with \
  "${missing_remaining_obligations_repo}" \
  "Missing required Phase 64.5 handoff term in docs/phase-64-5-phase66-limitation-handoff.md: Remaining Phase 66 proof obligations"

rc_overclaim_repo="${workdir}/rc-overclaim"
copy_valid_repo "${rc_overclaim_repo}"
printf '%s\n' "AegisOps is RC ready because Phase 64.5 has owners." >>"${rc_overclaim_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${rc_overclaim_repo}" \
  "Forbidden Phase 64.5 handoff claim in docs/phase-64-5-phase66-limitation-handoff.md: AegisOps is RC ready because Phase 64.5 has owners."

rc_ready_variant_repo="${workdir}/rc-ready-variant"
copy_valid_repo "${rc_ready_variant_repo}"
printf '%s\n' "AegisOps is RC-ready because Phase 64.5 has owners." >>"${rc_ready_variant_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${rc_ready_variant_repo}" \
  "Forbidden Phase 64.5 handoff claim in docs/phase-64-5-phase66-limitation-handoff.md: AegisOps is RC-ready because Phase 64.5 has owners."

readme_overclaim_repo="${workdir}/readme-overclaim"
copy_valid_repo "${readme_overclaim_repo}"
printf '%s\n' "AegisOps is GA ready because the handoff exists." >>"${readme_overclaim_repo}/README.md"
assert_fails_with \
  "${readme_overclaim_repo}" \
  "Forbidden Phase 64.5 handoff claim in README.md: AegisOps is GA ready because the handoff exists."

gate_truth_repo="${workdir}/gate-truth"
copy_valid_repo "${gate_truth_repo}"
printf '%s\n' "Handoff evidence is gate truth." >>"${gate_truth_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${gate_truth_repo}" \
  "Forbidden Phase 64.5 handoff claim in docs/phase-64-5-phase66-limitation-handoff.md: Handoff evidence is gate truth."

release_truth_repo="${workdir}/release-truth"
copy_valid_repo "${release_truth_repo}"
printf '%s\n' "Handoff evidence is release truth." >>"${release_truth_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${release_truth_repo}" \
  "Forbidden Phase 64.5 handoff claim in docs/phase-64-5-phase66-limitation-handoff.md: Handoff evidence is release truth."

production_ready_repo="${workdir}/production-ready"
copy_valid_repo "${production_ready_repo}"
printf '%s\n' "AegisOps is production ready because the handoff exists." >>"${production_ready_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${production_ready_repo}" \
  "Forbidden Phase 64.5 handoff claim in docs/phase-64-5-phase66-limitation-handoff.md: AegisOps is production ready because the handoff exists."

rc_gate_accepted_repo="${workdir}/rc-gate-accepted"
copy_valid_repo "${rc_gate_accepted_repo}"
printf '%s\n' "The RC gate is accepted by this handoff." >>"${rc_gate_accepted_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${rc_gate_accepted_repo}" \
  "Forbidden Phase 64.5 handoff claim in docs/phase-64-5-phase66-limitation-handoff.md: The RC gate is accepted by this handoff."

verifier_truth_repo="${workdir}/verifier-truth"
copy_valid_repo "${verifier_truth_repo}"
printf '%s\n' "Verifier output is readiness truth." >>"${verifier_truth_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${verifier_truth_repo}" \
  "Forbidden Phase 64.5 handoff claim in docs/phase-64-5-phase66-limitation-handoff.md: Verifier output is readiness truth."

issue_lint_truth_repo="${workdir}/issue-lint-truth"
copy_valid_repo "${issue_lint_truth_repo}"
printf '%s\n' "Issue-lint output is readiness truth." >>"${issue_lint_truth_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${issue_lint_truth_repo}" \
  "Forbidden Phase 64.5 handoff claim in docs/phase-64-5-phase66-limitation-handoff.md: Issue-lint output is readiness truth."

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 64.5 handoff: workstation-local absolute path detected"

echo "Phase 64.5 Phase 66 limitation handoff verifier tests passed."
