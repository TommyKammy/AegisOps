#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-55-7-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-55-closeout-evaluation.md" "${target}/docs/phase-55-closeout-evaluation.md"
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
  "Missing Phase 55 closeout evaluation: docs/phase-55-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 55\.7 closeout evaluation\]\(docs\/phase-55-closeout-evaluation\.md\)( records the guided first-user journey outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 56\/57\/58\/60\/66 handoff\.)/- Phase 55.7 closeout evaluation$1/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 55.7 closeout evaluation](docs/phase-55-closeout-evaluation.md)"

missing_readme_product_positioning_repo="${workdir}/missing-readme-product-positioning"
copy_valid_repo "${missing_readme_product_positioning_repo}"
perl -0pi -e 's/The Phase 55\.7 closeout evaluation is defined by the \[Phase 55\.7 closeout evaluation\]\(docs\/phase-55-closeout-evaluation\.md\)\./The Phase 55.7 closeout evaluation is defined by the Phase 55.7 closeout evaluation./' \
  "${missing_readme_product_positioning_repo}/README.md"
assert_fails_with \
  "${missing_readme_product_positioning_repo}" \
  "Missing README Product positioning reference: The Phase 55.7 closeout evaluation is defined by the [Phase 55.7 closeout evaluation](docs/phase-55-closeout-evaluation.md)."

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth\.//' \
  "${missing_authority_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 55 closeout term in docs/phase-55-closeout-evaluation.md: AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."

missing_failure_state_repo="${workdir}/missing-failure-state"
copy_valid_repo "${missing_failure_state_repo}"
perl -0pi -e 's/\| Failure states \| Checklist failure copy was not enumerated for common first-user blockers\. \| Phase 55\.5 adds bounded copy for missing Wazuh, missing Shuffle, missing secrets, port conflict, missing IdP, missing seed data, and protected-surface denial without authorizing repair or supportability completion\. \|\n//' \
  "${missing_failure_state_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${missing_failure_state_repo}" \
  'Missing required Phase 55 closeout term in docs/phase-55-closeout-evaluation.md: | Failure states | Checklist failure copy was not enumerated for common first-user blockers. | Phase 55.5 adds bounded copy for missing Wazuh, missing Shuffle, missing secrets, port conflict, missing IdP, missing seed data, and protected-surface denial without authorizing repair or supportability completion. |'

missing_phase60_handoff_repo="${workdir}/missing-phase60-handoff"
copy_valid_repo "${missing_phase60_handoff_repo}"
perl -0pi -e 's/Phase 60 can consume the Phase 55 demo report export skeleton as a demo-only export shape\.//' \
  "${missing_phase60_handoff_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${missing_phase60_handoff_repo}" \
  "Missing required Phase 55 closeout term in docs/phase-55-closeout-evaluation.md: Phase 60 can consume the Phase 55 demo report export skeleton as a demo-only export shape."

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/^- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1180 --config <supervisor-config-path>`: .*?\n//m' \
  "${missing_issue_lint_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing required Phase 55 closeout term in docs/phase-55-closeout-evaluation.md: node <codex-supervisor-root>/dist/index.js issue-lint 1180 --config <supervisor-config-path>"

phase56_overclaim_repo="${workdir}/phase56-overclaim"
copy_valid_repo "${phase56_overclaim_repo}"
printf '%s\n' "Phase 56 daily SOC workbench is complete" >>"${phase56_overclaim_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${phase56_overclaim_repo}" \
  "Forbidden Phase 55 closeout evaluation claim: Phase 56 daily SOC workbench is complete"

phase58_overclaim_repo="${workdir}/phase58-overclaim"
copy_valid_repo "${phase58_overclaim_repo}"
printf '%s\n' "Phase 58 supportability is complete" >>"${phase58_overclaim_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${phase58_overclaim_repo}" \
  "Forbidden Phase 55 closeout evaluation claim: Phase 58 supportability is complete"

phase62_overclaim_repo="${workdir}/phase62-overclaim"
copy_valid_repo "${phase62_overclaim_repo}"
printf '%s\n' "Phase 62 SOAR breadth is complete" >>"${phase62_overclaim_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${phase62_overclaim_repo}" \
  "Forbidden Phase 55 closeout evaluation claim: Phase 62 SOAR breadth is complete"

commercial_overclaim_repo="${workdir}/commercial-overclaim"
copy_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "Phase 55 proves commercial replacement readiness" >>"${commercial_overclaim_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${commercial_overclaim_repo}" \
  "Forbidden Phase 55 closeout evaluation claim: Phase 55 proves commercial replacement readiness"

demo_truth_repo="${workdir}/demo-truth"
copy_valid_repo "${demo_truth_repo}"
printf '%s\n' "Demo records are production truth" >>"${demo_truth_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${demo_truth_repo}" \
  "Forbidden Phase 55 closeout evaluation claim: Demo records are production truth"

ui_truth_repo="${workdir}/ui-truth"
copy_valid_repo "${ui_truth_repo}"
printf '%s\n' "Checklist UI state is workflow truth" >>"${ui_truth_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${ui_truth_repo}" \
  "Forbidden Phase 55 closeout evaluation claim: Checklist UI state is workflow truth"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-55-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 55 closeout evaluation: workstation-local absolute path detected"

echo "Phase 55 closeout evaluation verifier tests passed."
