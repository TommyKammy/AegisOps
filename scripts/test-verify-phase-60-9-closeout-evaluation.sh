#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-60-9-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-60-closeout-evaluation.md" "${target}/docs/phase-60-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-60-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

url_path_repo="${workdir}/url-path"
copy_valid_repo "${url_path_repo}"
windows_user_segment="Users"
printf '%s\n' \
  "Reference URL: https://example.com/home/docs/phase-60-closeout" \
  "Reference URL: https://example.com/Users/docs/phase-60-closeout" \
  "Reference URL: https://example.com/C:/${windows_user_segment}/docs/phase-60-closeout" \
  >>"${url_path_repo}/docs/phase-60-closeout-evaluation.md"
assert_passes "${url_path_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 60 closeout evaluation: docs/phase-60-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 60\.9 closeout evaluation\]\(docs\/phase-60-closeout-evaluation\.md\)[^\n]*\n/- Phase 60.9 closeout evaluation\\n/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 60.9 closeout evaluation](docs/phase-60-closeout-evaluation.md)"

missing_readme_product_positioning_repo="${workdir}/missing-readme-product-positioning"
copy_valid_repo "${missing_readme_product_positioning_repo}"
perl -0pi -e 's/The Phase 60\.9 closeout evaluation is defined by the \[Phase 60\.9 closeout evaluation\]\(docs\/phase-60-closeout-evaluation\.md\)\./The Phase 60.9 closeout evaluation is defined by the Phase 60.9 closeout evaluation./' \
  "${missing_readme_product_positioning_repo}/README.md"
assert_fails_with \
  "${missing_readme_product_positioning_repo}" \
  "Missing README Product positioning reference: The Phase 60.9 closeout evaluation is defined by the [Phase 60.9 closeout evaluation](docs/phase-60-closeout-evaluation.md)."

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
remove_doc_text "${missing_authority_repo}" \
  "AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action request, approval, action review, execution receipt, reconciliation, audit event, limitation, source health, and closeout truth."
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 60 closeout term in docs/phase-60-closeout-evaluation.md: AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action request, approval, action review, execution receipt, reconciliation, audit event, limitation, source health, and closeout truth."

missing_child_repo="${workdir}/missing-child"
copy_valid_repo "${missing_child_repo}"
remove_doc_text "${missing_child_repo}" \
  "| #1278 | Phase 60.9 Phase 60 closeout evaluation | Open until this document and focused closeout verifier land. |"
assert_fails_with \
  "${missing_child_repo}" \
  "Missing required Phase 60 closeout term in docs/phase-60-closeout-evaluation.md: | #1278 | Phase 60.9 Phase 60 closeout evaluation | Open until this document and focused closeout verifier land. |"

missing_prompt_evidence_repo="${workdir}/missing-prompt-evidence"
copy_valid_repo "${missing_prompt_evidence_repo}"
remove_doc_text "${missing_prompt_evidence_repo}" \
  "AI daily operations must reject missing authority ceilings, missing citations, disallowed authority, authority-expansion prompt pressure, stale evidence overclaims, conflicting evidence auto-resolution, treatment of advisory output as workflow truth, disabled/degraded AI workflow blocking, workspace-local path leakage, and Phase 61/62/66/Beta/RC/GA/commercial replacement overclaims."
assert_fails_with \
  "${missing_prompt_evidence_repo}" \
  "Missing required Phase 60 closeout term in docs/phase-60-closeout-evaluation.md: AI daily operations must reject missing authority ceilings"

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1278 --config <supervisor-config-path>`.*\n//m' \
  "${missing_issue_lint_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  'Missing required Phase 60 closeout term in docs/phase-60-closeout-evaluation.md: `node <codex-supervisor-root>/dist/index.js issue-lint 1278 --config <supervisor-config-path>`'

phase61_overclaim_repo="${workdir}/phase61-overclaim"
copy_valid_repo "${phase61_overclaim_repo}"
printf '%s\n' "Phase 61 SIEM breadth is complete" >>"${phase61_overclaim_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${phase61_overclaim_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: Phase 61 SIEM breadth is complete"

phase62_overclaim_repo="${workdir}/phase62-overclaim"
copy_valid_repo "${phase62_overclaim_repo}"
printf '%s\n' "Phase 62 SOAR breadth is complete" >>"${phase62_overclaim_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${phase62_overclaim_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: Phase 62 SOAR breadth is complete"

commercial_overclaim_repo="${workdir}/commercial-overclaim"
copy_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "AegisOps is a commercial replacement for every SIEM/SOAR capability" >>"${commercial_overclaim_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${commercial_overclaim_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: AegisOps is a commercial replacement for every SIEM/SOAR capability"

ai_truth_repo="${workdir}/ai-truth"
copy_valid_repo "${ai_truth_repo}"
printf '%s\n' "AI output is workflow truth" >>"${ai_truth_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${ai_truth_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: AI output is workflow truth"

disabled_ai_block_repo="${workdir}/disabled-ai-block"
copy_valid_repo "${disabled_ai_block_repo}"
printf '%s\n' "Disabled AI may block case review" >>"${disabled_ai_block_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${disabled_ai_block_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: Disabled AI may block case review"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
printf 'Run /%s/example/Dev/codex-supervisor/dist/index.js.\n' "Users" >>"${absolute_path_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 60 closeout evaluation: workstation-local absolute path detected"

absolute_path_windows_backslash_repo="${workdir}/absolute-path-windows-backslash"
copy_valid_repo "${absolute_path_windows_backslash_repo}"
printf 'Run C:\\%s\\example\\Dev\\codex-supervisor\\dist\\index.js.\n' "Users" >>"${absolute_path_windows_backslash_repo}/docs/phase-60-closeout-evaluation.md"
printf 'Run "C:\\%s\\example\\Dev\\codex-supervisor\\dist\\index.js".\n' "Users" >>"${absolute_path_windows_backslash_repo}/docs/phase-60-closeout-evaluation.md"
printf 'Run `C:\\%s\\example\\Dev\\codex-supervisor\\dist\\index.js`.\n' "Users" >>"${absolute_path_windows_backslash_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_windows_backslash_repo}" \
  "Forbidden Phase 60 closeout evaluation: workstation-local absolute path detected"

overclaim_disabled_repo="${workdir}/overclaim-disabled-degraded"
copy_valid_repo "${overclaim_disabled_repo}"
printf '%s\n' "AI can be disabled or degraded to block case review." >>"${overclaim_disabled_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${overclaim_disabled_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: AI can be disabled or degraded to block case review"

overclaim_approval_plain_repo="${workdir}/overclaim-plain-approval"
copy_valid_repo "${overclaim_approval_plain_repo}"
printf '%s\n' "AI may approve actions" >>"${overclaim_approval_plain_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${overclaim_approval_plain_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: AI may approve actions"

overclaim_execute_plain_repo="${workdir}/overclaim-plain-execute"
copy_valid_repo "${overclaim_execute_plain_repo}"
printf '%s\n' "AI may execute actions" >>"${overclaim_execute_plain_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${overclaim_execute_plain_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: AI may execute actions"

overclaim_degraded_cap_repo="${workdir}/overclaim-degraded-capitalized"
copy_valid_repo "${overclaim_degraded_cap_repo}"
printf '%s\n' "Degraded AI may block case review" >>"${overclaim_degraded_cap_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${overclaim_degraded_cap_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: Degraded AI may block case review"

overclaim_conflict_repo="${workdir}/overclaim-conflict-autoresolve"
copy_valid_repo "${overclaim_conflict_repo}"
printf '%s\n' "Conflicting evidence may be automatically resolved." >>"${overclaim_conflict_repo}/docs/phase-60-closeout-evaluation.md"
assert_fails_with \
  "${overclaim_conflict_repo}" \
  "Forbidden Phase 60 closeout evaluation claim: conflicting evidence may be automatically resolved"

echo "Phase 60 closeout verification tests passed."
