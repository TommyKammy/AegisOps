#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-56-8-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-56-closeout-evaluation.md" "${target}/docs/phase-56-closeout-evaluation.md"
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
  "Missing Phase 56 closeout evaluation: docs/phase-56-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 56\.8 closeout evaluation\]\(docs\/phase-56-closeout-evaluation\.md\)( records the Daily SOC Workbench outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 57\/58\/59\/60\/66 handoff\.)/- Phase 56.8 closeout evaluation$1/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 56.8 closeout evaluation](docs/phase-56-closeout-evaluation.md)"

missing_readme_product_positioning_repo="${workdir}/missing-readme-product-positioning"
copy_valid_repo "${missing_readme_product_positioning_repo}"
perl -0pi -e 's/The Phase 56\.8 closeout evaluation is defined by the \[Phase 56\.8 closeout evaluation\]\(docs\/phase-56-closeout-evaluation\.md\)\./The Phase 56.8 closeout evaluation is defined by the Phase 56.8 closeout evaluation./' \
  "${missing_readme_product_positioning_repo}/README.md"
assert_fails_with \
  "${missing_readme_product_positioning_repo}" \
  "Missing README Product positioning reference: The Phase 56.8 closeout evaluation is defined by the [Phase 56.8 closeout evaluation](docs/phase-56-closeout-evaluation.md)."

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth\.//' \
  "${missing_authority_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 56 closeout term in docs/phase-56-closeout-evaluation.md: AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."

missing_today_row_repo="${workdir}/missing-today-row"
copy_valid_repo "${missing_today_row_repo}"
perl -0pi -e 's/\| Today UI \| Operators had first-login guidance and case\/action surfaces, but no Today starting point for repeated daily review\. \| Phase 56\.2 renders Today work focus, empty state, degraded\/stale badges, pending approvals, mismatches, evidence gaps, advisory AI focus, and stale-cache refusal\. \|\n//' \
  "${missing_today_row_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${missing_today_row_repo}" \
  'Missing required Phase 56 closeout term in docs/phase-56-closeout-evaluation.md: | Today UI | Operators had first-login guidance and case/action surfaces, but no Today starting point for repeated daily review. | Phase 56.2 renders Today work focus, empty state, degraded/stale badges, pending approvals, mismatches, evidence gaps, advisory AI focus, and stale-cache refusal. |'

missing_negative_evidence_repo="${workdir}/missing-negative-evidence"
copy_valid_repo "${missing_negative_evidence_repo}"
perl -0pi -e 's/Today UI tests reject stale cache or malformed backend data and fail closed when a reread fails after cached data exists\.//' \
  "${missing_negative_evidence_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${missing_negative_evidence_repo}" \
  "Missing required Phase 56 closeout term in docs/phase-56-closeout-evaluation.md: Today UI tests reject stale cache or malformed backend data and fail closed when a reread fails after cached data exists."

missing_phase59_handoff_repo="${workdir}/missing-phase59-handoff"
copy_valid_repo "${missing_phase59_handoff_repo}"
perl -0pi -e 's/Phase 59 can consume the Phase 56 advisory-only AI focus and accepted\/rejected AI summary handling as bounded operator-context evidence\.//' \
  "${missing_phase59_handoff_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${missing_phase59_handoff_repo}" \
  "Missing required Phase 56 closeout term in docs/phase-56-closeout-evaluation.md: Phase 59 can consume the Phase 56 advisory-only AI focus and accepted/rejected AI summary handling as bounded operator-context evidence."

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/^- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1197 --config <supervisor-config-path>`: .*?\n//m' \
  "${missing_issue_lint_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing required Phase 56 closeout term in docs/phase-56-closeout-evaluation.md: node <codex-supervisor-root>/dist/index.js issue-lint 1197 --config <supervisor-config-path>"

phase57_overclaim_repo="${workdir}/phase57-overclaim"
copy_valid_repo "${phase57_overclaim_repo}"
printf '%s\n' "Phase 57 admin/RBAC/source/action policy is complete" >>"${phase57_overclaim_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${phase57_overclaim_repo}" \
  "Forbidden Phase 56 closeout evaluation claim: Phase 57 admin/RBAC/source/action policy is complete"

phase58_overclaim_repo="${workdir}/phase58-overclaim"
copy_valid_repo "${phase58_overclaim_repo}"
printf '%s\n' "Phase 58 supportability is complete" >>"${phase58_overclaim_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${phase58_overclaim_repo}" \
  "Forbidden Phase 56 closeout evaluation claim: Phase 58 supportability is complete"

phase60_overclaim_repo="${workdir}/phase60-overclaim"
copy_valid_repo "${phase60_overclaim_repo}"
printf '%s\n' "Phase 60 audit or reporting breadth is complete" >>"${phase60_overclaim_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${phase60_overclaim_repo}" \
  "Forbidden Phase 56 closeout evaluation claim: Phase 60 audit or reporting breadth is complete"

commercial_overclaim_repo="${workdir}/commercial-overclaim"
copy_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "Phase 56 proves commercial replacement readiness" >>"${commercial_overclaim_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${commercial_overclaim_repo}" \
  "Forbidden Phase 56 closeout evaluation claim: Phase 56 proves commercial replacement readiness"

ui_truth_repo="${workdir}/ui-truth"
copy_valid_repo "${ui_truth_repo}"
printf '%s\n' "Stale UI cache is current workflow truth" >>"${ui_truth_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${ui_truth_repo}" \
  "Forbidden Phase 56 closeout evaluation claim: Stale UI cache is current workflow truth"

handoff_truth_repo="${workdir}/handoff-truth"
copy_valid_repo "${handoff_truth_repo}"
printf '%s\n' "Business-hours handoff copy is closeout truth" >>"${handoff_truth_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${handoff_truth_repo}" \
  "Forbidden Phase 56 closeout evaluation claim: Business-hours handoff copy is closeout truth"

health_truth_repo="${workdir}/health-truth"
copy_valid_repo "${health_truth_repo}"
printf '%s\n' "Health summary is release gate truth" >>"${health_truth_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${health_truth_repo}" \
  "Forbidden Phase 56 closeout evaluation claim: Health summary is release gate truth"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-56-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 56 closeout evaluation: workstation-local absolute path detected"

echo "Phase 56 closeout evaluation verifier tests passed."
