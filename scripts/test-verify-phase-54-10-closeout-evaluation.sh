#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-54-10-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-54-closeout-evaluation.md" "${target}/docs/phase-54-closeout-evaluation.md"
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
  "Missing Phase 54 closeout evaluation: docs/phase-54-closeout-evaluation.md"

missing_readme_link_repo="${workdir}/missing-readme-link"
copy_valid_repo "${missing_readme_link_repo}"
perl -0pi -e 's/\[Phase 54\.10 closeout evaluation\]\(docs\/phase-54-closeout-evaluation\.md\)/Phase 54.10 closeout evaluation/g' \
  "${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "Missing README Phase 54.10 closeout link: [Phase 54.10 closeout evaluation](docs/phase-54-closeout-evaluation.md)"

missing_subordinate_posture_repo="${workdir}/missing-subordinate-posture"
copy_valid_repo "${missing_subordinate_posture_repo}"
perl -0pi -e 's/Shuffle remains a subordinate routine automation substrate\.//' \
  "${missing_subordinate_posture_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${missing_subordinate_posture_repo}" \
  "Missing required Phase 54 closeout term in docs/phase-54-closeout-evaluation.md: Shuffle remains a subordinate routine automation substrate."

missing_workflow_template_repo="${workdir}/missing-workflow-template"
copy_valid_repo "${missing_workflow_template_repo}"
perl -0pi -e 's/\| Workflow template contract \| Generic delegated-execution expectations from earlier action policy work\. \| Reviewed workflow template metadata requires correlation, action request, approval decision, execution receipt, version, owner, reviewed status, callback URL, and trusted callback secret reference before import\. \|\n//' \
  "${missing_workflow_template_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${missing_workflow_template_repo}" \
  'Missing required Phase 54 closeout term in docs/phase-54-closeout-evaluation.md: | Workflow template contract | Generic delegated-execution expectations from earlier action policy work. | Reviewed workflow template metadata requires correlation, action request, approval decision, execution receipt, version, owner, reviewed status, callback URL, and trusted callback secret reference before import. |'

missing_delegation_binding_repo="${workdir}/missing-delegation-binding"
copy_valid_repo "${missing_delegation_binding_repo}"
perl -0pi -e 's/\| Delegation binding \| Shuffle dispatch could rely on generic approved action request routing\. \| AegisOps-to-Shuffle dispatch requires explicit `shuffle_delegation_binding` fields, reviewed workflow version, correlation id, expected execution receipt id, and requested-scope match before adapter dispatch\. \|\n//' \
  "${missing_delegation_binding_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${missing_delegation_binding_repo}" \
  'Missing required Phase 54 closeout term in docs/phase-54-closeout-evaluation.md: | Delegation binding | Shuffle dispatch could rely on generic approved action request routing. | AegisOps-to-Shuffle dispatch requires explicit `shuffle_delegation_binding` fields, reviewed workflow version, correlation id, expected execution receipt id, and requested-scope match before adapter dispatch. |'

missing_receipt_repo="${workdir}/missing-receipt"
copy_valid_repo "${missing_receipt_repo}"
perl -0pi -e 's/\| Receipt normalization \| Downstream receipt handling was not pinned to the Phase 54 profile contract\. \| Shuffle receipts are normalized into AegisOps execution receipt context only when the observed run, delegation id, expected receipt id, approval id, payload hash, idempotency key, and coordination binding match the authoritative action execution\. \|\n//' \
  "${missing_receipt_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${missing_receipt_repo}" \
  'Missing required Phase 54 closeout term in docs/phase-54-closeout-evaluation.md: | Receipt normalization | Downstream receipt handling was not pinned to the Phase 54 profile contract. | Shuffle receipts are normalized into AegisOps execution receipt context only when the observed run, delegation id, expected receipt id, approval id, payload hash, idempotency key, and coordination binding match the authoritative action execution. |'

missing_manual_fallback_repo="${workdir}/missing-manual-fallback"
copy_valid_repo "${missing_manual_fallback_repo}"
perl -0pi -e 's/\| Manual fallback \| Unavailable or rejected Shuffle paths did not have a Phase 54 manual fallback artifact\. \| Manual fallback requires owner, operator note, affected template\/action, expected evidence, and blocked, unavailable, rejected, missing receipt, stale receipt, or mismatched receipt reason\. \|\n//' \
  "${missing_manual_fallback_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${missing_manual_fallback_repo}" \
  'Missing required Phase 54 closeout term in docs/phase-54-closeout-evaluation.md: | Manual fallback | Unavailable or rejected Shuffle paths did not have a Phase 54 manual fallback artifact. | Manual fallback requires owner, operator note, affected template/action, expected evidence, and blocked, unavailable, rejected, missing receipt, stale receipt, or mismatched receipt reason. |'

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/^- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1161 --config <supervisor-config-path>`: .*?\n//m' \
  "${missing_issue_lint_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing required Phase 54 closeout term in docs/phase-54-closeout-evaluation.md: node <codex-supervisor-root>/dist/index.js issue-lint 1161 --config <supervisor-config-path>"

phase62_overclaim_repo="${workdir}/phase62-overclaim"
copy_valid_repo "${phase62_overclaim_repo}"
printf '%s\n' "Phase 62 SOAR breadth is complete" >>"${phase62_overclaim_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${phase62_overclaim_repo}" \
  "Forbidden Phase 54 closeout evaluation claim: Phase 62 SOAR breadth is complete"

phase62_contradictory_overclaim_repo="${workdir}/phase62-contradictory-overclaim"
copy_valid_repo "${phase62_contradictory_overclaim_repo}"
printf '%s\n' "This closeout does not claim Phase 62 SOAR breadth is complete, but Phase 62 SOAR breadth is complete." >>"${phase62_contradictory_overclaim_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${phase62_contradictory_overclaim_repo}" \
  "Forbidden Phase 54 closeout evaluation claim: Phase 62 SOAR breadth is complete"

rc_overclaim_repo="${workdir}/rc-overclaim"
copy_valid_repo "${rc_overclaim_repo}"
printf '%s\n' "Phase 54 proves RC readiness" >>"${rc_overclaim_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${rc_overclaim_repo}" \
  "Forbidden Phase 54 closeout evaluation claim: Phase 54 proves RC readiness"

shuffle_truth_repo="${workdir}/shuffle-truth"
copy_valid_repo "${shuffle_truth_repo}"
printf '%s\n' "Shuffle success is AegisOps reconciliation truth" >>"${shuffle_truth_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${shuffle_truth_repo}" \
  "Forbidden Phase 54 closeout evaluation claim: Shuffle success is AegisOps reconciliation truth"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-54-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 54 closeout evaluation: workstation-local absolute path detected"

echo "Phase 54 closeout evaluation verifier tests passed."
