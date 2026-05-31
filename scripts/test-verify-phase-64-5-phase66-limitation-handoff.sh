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

missing_reviewed_record_repo="${workdir}/missing-reviewed-record"
copy_valid_repo "${missing_reviewed_record_repo}"
perl -0pi -e 's/\| `limitation-phase64-rc-gate-consumption-001`[^\n]*\n//' \
  "${missing_reviewed_record_repo}/docs/phase-64-1-reviewed-limitation-ownership-records.md"
assert_fails_with \
  "${missing_reviewed_record_repo}" \
  "Missing required Phase 64.1 reviewed limitation record term"

missing_row_blocker_repo="${workdir}/missing-row-blocker"
copy_valid_repo "${missing_row_blocker_repo}"
remove_doc_text "${missing_row_blocker_repo}" "RC gate packet must still prove install, Wazuh signal, Shuffle execution, AI trace, report export, restore dry-run, upgrade plan, support bundle, and limitations ownership evidence against the approved RC gate."
assert_fails_with \
  "${missing_row_blocker_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-rc-gate-consumption-001: missing open blockers"

malformed_extra_row_repo="${workdir}/malformed-extra-row"
copy_valid_repo "${malformed_extra_row_repo}"
perl -0pi -e 's/\| `limitation-phase64-support-bundle-001`/\|`limitation-phase64-extra-002`\| \| \| \| \| \| \| \|\n| `limitation-phase64-support-bundle-001`/' \
  "${malformed_extra_row_repo}/docs/phase-64-5-phase66-limitation-handoff.md"
assert_fails_with \
  "${malformed_extra_row_repo}" \
  "Invalid Phase 64.5 handoff row for limitation-phase64-extra-002: missing owner"

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
