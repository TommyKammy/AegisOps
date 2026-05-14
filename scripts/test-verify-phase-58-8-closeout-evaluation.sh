#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-58-8-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-58-closeout-evaluation.md" "${target}/docs/phase-58-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-58-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

url_path_repo="${workdir}/url-path"
copy_valid_repo "${url_path_repo}"
windows_user_segment="Users"
linux_home_segment="home"
printf '%s\n' \
  "Reference URL: https://example.com/${linux_home_segment}/docs/phase-58-closeout" \
  "Reference URL: https://example.com/${windows_user_segment}/docs/phase-58-closeout" \
  "Reference URL: https://example.com/C:/${windows_user_segment}/docs/phase-58-closeout" \
  >>"${url_path_repo}/docs/phase-58-closeout-evaluation.md"
assert_passes "${url_path_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 58 closeout evaluation: docs/phase-58-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 58\.8 closeout evaluation\]\(docs\/phase-58-closeout-evaluation\.md\)( records the supportability MVP outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 59\/60\/66 handoff\.)/- Phase 58.8 closeout evaluation$1/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 58.8 closeout evaluation](docs/phase-58-closeout-evaluation.md)"

missing_readme_product_positioning_repo="${workdir}/missing-readme-product-positioning"
copy_valid_repo "${missing_readme_product_positioning_repo}"
perl -0pi -e 's/The Phase 58\.8 closeout evaluation is defined by the \[Phase 58\.8 closeout evaluation\]\(docs\/phase-58-closeout-evaluation\.md\)\./The Phase 58.8 closeout evaluation is defined by the Phase 58.8 closeout evaluation./' \
  "${missing_readme_product_positioning_repo}/README.md"
assert_fails_with \
  "${missing_readme_product_positioning_repo}" \
  "Missing README Product positioning reference: The Phase 58.8 closeout evaluation is defined by the [Phase 58.8 closeout evaluation](docs/phase-58-closeout-evaluation.md)."

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
remove_doc_text "${missing_authority_repo}" \
  "AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event, limitation, release, gate, restore, workflow, and closeout truth."
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 58 closeout term in docs/phase-58-closeout-evaluation.md: AegisOps control-plane records remain authoritative"

missing_restore_row_repo="${workdir}/missing-restore-row"
copy_valid_repo "${missing_restore_row_repo}"
remove_doc_text "${missing_restore_row_repo}" \
  "| Restore dry-run | Restore validation existed, but there was no explicit read-only preflight command for reviewed backup payloads. | Phase 58.4 adds dry-run preflight evidence that validates payload shape, provenance, source/profile binding, staleness, duplicates, and clean restore target requirements before live restore review. |"
assert_fails_with \
  "${missing_restore_row_repo}" \
  "Missing required Phase 58 closeout term in docs/phase-58-closeout-evaluation.md: | Restore dry-run | Restore validation existed"

missing_pr_evidence_repo="${workdir}/missing-pr-evidence"
copy_valid_repo "${missing_pr_evidence_repo}"
remove_doc_text "${missing_pr_evidence_repo}" \
  "| #1250 | Phase 58.7 supportability UI/CLI summary | Merged read-only supportability summary CLI/runtime/tests; no separate new UI route is claimed by this closeout. |"
assert_fails_with \
  "${missing_pr_evidence_repo}" \
  "Missing required Phase 58 closeout term in docs/phase-58-closeout-evaluation.md: | #1250 | Phase 58.7 supportability UI/CLI summary"

missing_negative_evidence_repo="${workdir}/missing-negative-evidence"
copy_valid_repo "${missing_negative_evidence_repo}"
remove_doc_text "${missing_negative_evidence_repo}" \
  "Support bundle redaction verifier tests reject secret-looking values, authorization headers, credential URLs, cert material, private keys, workstation-local paths, private payloads, private ticket content, support bundle as workflow truth, support collaborator operator expansion, and missing redaction manifest coverage."
assert_fails_with \
  "${missing_negative_evidence_repo}" \
  "Missing required Phase 58 closeout term in docs/phase-58-closeout-evaluation.md: Support bundle redaction verifier tests reject secret-looking values"

missing_phase59_handoff_repo="${workdir}/missing-phase59-handoff"
copy_valid_repo "${missing_phase59_handoff_repo}"
remove_doc_text "${missing_phase59_handoff_repo}" \
  "Phase 59 can consume the Phase 58 doctor explanation pattern, degraded AI posture reporting, support links, negative-authority vocabulary, and supportability summary boundaries as operational context."
assert_fails_with \
  "${missing_phase59_handoff_repo}" \
  "Missing required Phase 58 closeout term in docs/phase-58-closeout-evaluation.md: Phase 59 can consume the Phase 58 doctor explanation pattern"

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/^- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1242 --config <supervisor-config-path>`: .*?\n//m' \
  "${missing_issue_lint_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing required Phase 58 closeout term in docs/phase-58-closeout-evaluation.md: node <codex-supervisor-root>/dist/index.js issue-lint 1242 --config <supervisor-config-path>"

phase59_overclaim_repo="${workdir}/phase59-overclaim"
copy_valid_repo "${phase59_overclaim_repo}"
printf '%s\n' "Phase 59 AI daily operations is complete" >>"${phase59_overclaim_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${phase59_overclaim_repo}" \
  "Forbidden Phase 58 closeout evaluation claim: Phase 59 AI daily operations is complete"

commercial_overclaim_repo="${workdir}/commercial-overclaim"
copy_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "Phase 58 proves commercial replacement readiness" >>"${commercial_overclaim_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${commercial_overclaim_repo}" \
  "Forbidden Phase 58 closeout evaluation claim: Phase 58 proves commercial replacement readiness"

doctor_truth_repo="${workdir}/doctor-truth"
copy_valid_repo "${doctor_truth_repo}"
printf '%s\n' "Doctor output is workflow truth" >>"${doctor_truth_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${doctor_truth_repo}" \
  "Forbidden Phase 58 closeout evaluation claim: Doctor output is workflow truth"

backup_restore_truth_repo="${workdir}/backup-restore-truth"
copy_valid_repo "${backup_restore_truth_repo}"
printf '%s\n' "Backup manifest proves restore success" >>"${backup_restore_truth_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${backup_restore_truth_repo}" \
  "Forbidden Phase 58 closeout evaluation claim: Backup manifest proves restore success"

dry_run_truth_repo="${workdir}/dry-run-truth"
copy_valid_repo "${dry_run_truth_repo}"
printf '%s\n' "Restore dry-run proves live restore completion" >>"${dry_run_truth_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${dry_run_truth_repo}" \
  "Forbidden Phase 58 closeout evaluation claim: Restore dry-run proves live restore completion"

upgrade_execution_repo="${workdir}/upgrade-execution"
copy_valid_repo "${upgrade_execution_repo}"
printf '%s\n' "Upgrade plan executes live upgrades" >>"${upgrade_execution_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${upgrade_execution_repo}" \
  "Forbidden Phase 58 closeout evaluation claim: Upgrade plan executes live upgrades"

support_authority_repo="${workdir}/support-authority"
copy_valid_repo "${support_authority_repo}"
printf '%s\n' "Support collaborator has operator authority" >>"${support_authority_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${support_authority_repo}" \
  "Forbidden Phase 58 closeout evaluation claim: Support collaborator has operator authority"

summary_release_truth_repo="${workdir}/summary-release-truth"
copy_valid_repo "${summary_release_truth_repo}"
printf '%s\n' "Supportability summary is release truth" >>"${summary_release_truth_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${summary_release_truth_repo}" \
  "Forbidden Phase 58 closeout evaluation claim: Supportability summary is release truth"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 58 closeout evaluation: workstation-local absolute path detected"

absolute_path_windows_backslash_repo="${workdir}/absolute-path-windows-backslash"
copy_valid_repo "${absolute_path_windows_backslash_repo}"
windows_drive="C:"
windows_home_dir="Users"
printf 'Run %s\\%s\\example\\Dev\\codex-supervisor\\dist\\index.js.\n' "${windows_drive}" "${windows_home_dir}" >>"${absolute_path_windows_backslash_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_windows_backslash_repo}" \
  "Forbidden Phase 58 closeout evaluation: workstation-local absolute path detected"

absolute_path_windows_slash_repo="${workdir}/absolute-path-windows-slash"
copy_valid_repo "${absolute_path_windows_slash_repo}"
printf 'Run %s/%s/example/Dev/codex-supervisor/dist/index.js.\n' "${windows_drive}" "${windows_home_dir}" >>"${absolute_path_windows_slash_repo}/docs/phase-58-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_windows_slash_repo}" \
  "Forbidden Phase 58 closeout evaluation: workstation-local absolute path detected"

echo "Phase 58 closeout evaluation verifier tests passed."
