#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-57-8-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-57-closeout-evaluation.md" "${target}/docs/phase-57-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 57 closeout evaluation: docs/phase-57-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 57\.8 closeout evaluation\]\(docs\/phase-57-closeout-evaluation\.md\)( records the commercial administration MVP outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 58\/59\/60\/66 handoff\.)/- Phase 57.8 closeout evaluation$1/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 57.8 closeout evaluation](docs/phase-57-closeout-evaluation.md)"

missing_readme_product_positioning_repo="${workdir}/missing-readme-product-positioning"
copy_valid_repo "${missing_readme_product_positioning_repo}"
perl -0pi -e 's/The Phase 57\.8 closeout evaluation is defined by the \[Phase 57\.8 closeout evaluation\]\(docs\/phase-57-closeout-evaluation\.md\)\./The Phase 57.8 closeout evaluation is defined by the Phase 57.8 closeout evaluation./' \
  "${missing_readme_product_positioning_repo}/README.md"
assert_fails_with \
  "${missing_readme_product_positioning_repo}" \
  "Missing README Product positioning reference: The Phase 57.8 closeout evaluation is defined by the [Phase 57.8 closeout evaluation](docs/phase-57-closeout-evaluation.md)."

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event truth, limitation, release, gate, and closeout truth\.//' \
  "${missing_authority_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 57 closeout term in docs/phase-57-closeout-evaluation.md: AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event truth, limitation, release, gate, and closeout truth."

missing_source_row_repo="${workdir}/missing-source-row"
copy_valid_repo "${missing_source_row_repo}"
perl -0pi -e 's/\| Source profile admin \| Source posture was represented by reviewed Wazuh contracts, but no bounded admin surface\. \| Phase 57\.3 renders Wazuh and future reviewed source profile posture for create, update, disable, degraded, and audit-trail states without source marketplace claims\. \|\n//' \
  "${missing_source_row_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${missing_source_row_repo}" \
  'Missing required Phase 57 closeout term in docs/phase-57-closeout-evaluation.md: | Source profile admin | Source posture was represented by reviewed Wazuh contracts, but no bounded admin surface. | Phase 57.3 renders Wazuh and future reviewed source profile posture for create, update, disable, degraded, and audit-trail states without source marketplace claims. |'

missing_negative_evidence_repo="${workdir}/missing-negative-evidence"
copy_valid_repo "${missing_negative_evidence_repo}"
perl -0pi -e 's/Retention policy admin tests reject locked or export-pending deletion, active workflow closure, audit erasure, historical record-chain rewrite, policy-as-closeout, and stale retention cache authority\.//' \
  "${missing_negative_evidence_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${missing_negative_evidence_repo}" \
  "Missing required Phase 57 closeout term in docs/phase-57-closeout-evaluation.md: Retention policy admin tests reject locked or export-pending deletion, active workflow closure, audit erasure, historical record-chain rewrite, policy-as-closeout, and stale retention cache authority."

missing_phase59_handoff_repo="${workdir}/missing-phase59-handoff"
copy_valid_repo "${missing_phase59_handoff_repo}"
perl -0pi -e 's/Phase 59 can consume the Phase 57 AI enablement posture as bounded enablement evidence\.//' \
  "${missing_phase59_handoff_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${missing_phase59_handoff_repo}" \
  "Missing required Phase 57 closeout term in docs/phase-57-closeout-evaluation.md: Phase 59 can consume the Phase 57 AI enablement posture as bounded enablement evidence."

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/^- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1214 --config <supervisor-config-path>`: .*?\n//m' \
  "${missing_issue_lint_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing required Phase 57 closeout term in docs/phase-57-closeout-evaluation.md: node <codex-supervisor-root>/dist/index.js issue-lint 1214 --config <supervisor-config-path>"

phase58_overclaim_repo="${workdir}/phase58-overclaim"
copy_valid_repo "${phase58_overclaim_repo}"
printf '%s\n' "Phase 58 supportability is complete" >>"${phase58_overclaim_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${phase58_overclaim_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Phase 58 supportability is complete"

phase59_overclaim_repo="${workdir}/phase59-overclaim"
copy_valid_repo "${phase59_overclaim_repo}"
printf '%s\n' "Phase 59 AI daily operations is complete" >>"${phase59_overclaim_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${phase59_overclaim_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Phase 59 AI daily operations is complete"

phase60_overclaim_repo="${workdir}/phase60-overclaim"
copy_valid_repo "${phase60_overclaim_repo}"
printf '%s\n' "Phase 60 audit or reporting breadth is complete" >>"${phase60_overclaim_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${phase60_overclaim_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Phase 60 audit or reporting breadth is complete"

commercial_overclaim_repo="${workdir}/commercial-overclaim"
copy_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "Phase 57 proves commercial replacement readiness" >>"${commercial_overclaim_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${commercial_overclaim_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Phase 57 proves commercial replacement readiness"

support_authority_repo="${workdir}/support-authority"
copy_valid_repo "${support_authority_repo}"
printf '%s\n' "Support operator workflow authority is enabled" >>"${support_authority_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${support_authority_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Support operator workflow authority is enabled"

hard_write_repo="${workdir}/hard-write"
copy_valid_repo "${hard_write_repo}"
printf '%s\n' "Hard Write default enablement is allowed" >>"${hard_write_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${hard_write_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Hard Write default enablement is allowed"

retention_delete_repo="${workdir}/retention-delete"
copy_valid_repo "${retention_delete_repo}"
printf '%s\n' "Retention policy deletes locked records" >>"${retention_delete_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${retention_delete_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Retention policy deletes locked records"

audit_truth_repo="${workdir}/audit-truth"
copy_valid_repo "${audit_truth_repo}"
printf '%s\n' "Audit export config is audit truth" >>"${audit_truth_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${audit_truth_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Audit export config is audit truth"

ai_scope_repo="${workdir}/ai-scope"
copy_valid_repo "${ai_scope_repo}"
printf '%s\n' "AI enablement toggle adds new AI features" >>"${ai_scope_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${ai_scope_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: AI enablement toggle adds new AI features"

admin_truth_repo="${workdir}/admin-truth"
copy_valid_repo "${admin_truth_repo}"
printf '%s\n' "Admin config rewrites historical workflow truth" >>"${admin_truth_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${admin_truth_repo}" \
  "Forbidden Phase 57 closeout evaluation claim: Admin config rewrites historical workflow truth"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 57 closeout evaluation: workstation-local absolute path detected"

absolute_path_windows_backslash_repo="${workdir}/absolute-path-windows-backslash"
copy_valid_repo "${absolute_path_windows_backslash_repo}"
windows_drive="C:"
windows_home_dir="Users"
printf 'Run %s\\%s\\example\\Dev\\codex-supervisor\\dist\\index.js.\n' "${windows_drive}" "${windows_home_dir}" >>"${absolute_path_windows_backslash_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_windows_backslash_repo}" \
  "Forbidden Phase 57 closeout evaluation: workstation-local absolute path detected"

absolute_path_windows_slash_repo="${workdir}/absolute-path-windows-slash"
copy_valid_repo "${absolute_path_windows_slash_repo}"
printf 'Run %s/%s/example/Dev/codex-supervisor/dist/index.js.\n' "${windows_drive}" "${windows_home_dir}" >>"${absolute_path_windows_slash_repo}/docs/phase-57-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_windows_slash_repo}" \
  "Forbidden Phase 57 closeout evaluation: workstation-local absolute path detected"

echo "Phase 57 closeout evaluation verifier tests passed."
