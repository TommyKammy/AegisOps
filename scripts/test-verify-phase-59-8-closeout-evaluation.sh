#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-59-8-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-59-closeout-evaluation.md" "${target}/docs/phase-59-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-59-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

url_path_repo="${workdir}/url-path"
copy_valid_repo "${url_path_repo}"
windows_user_segment="Users"
linux_home_segment="home"
printf '%s\n' \
  "Reference URL: https://example.com/${linux_home_segment}/docs/phase-59-closeout" \
  "Reference URL: https://example.com/${windows_user_segment}/docs/phase-59-closeout" \
  "Reference URL: https://example.com/C:/${windows_user_segment}/docs/phase-59-closeout" \
  >>"${url_path_repo}/docs/phase-59-closeout-evaluation.md"
assert_passes "${url_path_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 59 closeout evaluation: docs/phase-59-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 59\.8 closeout evaluation\]\(docs\/phase-59-closeout-evaluation\.md\)( records the AI governance foundation outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 60\/66 handoff\.)/- Phase 59.8 closeout evaluation$1/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 59.8 closeout evaluation](docs/phase-59-closeout-evaluation.md)"

missing_readme_product_positioning_repo="${workdir}/missing-readme-product-positioning"
copy_valid_repo "${missing_readme_product_positioning_repo}"
perl -0pi -e 's/The Phase 59\.8 closeout evaluation is defined by the \[Phase 59\.8 closeout evaluation\]\(docs\/phase-59-closeout-evaluation\.md\)\./The Phase 59.8 closeout evaluation is defined by the Phase 59.8 closeout evaluation./' \
  "${missing_readme_product_positioning_repo}/README.md"
assert_fails_with \
  "${missing_readme_product_positioning_repo}" \
  "Missing README Product positioning reference: The Phase 59.8 closeout evaluation is defined by the [Phase 59.8 closeout evaluation](docs/phase-59-closeout-evaluation.md)."

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
remove_doc_text "${missing_authority_repo}" \
  "AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event, limitation, release, gate, workflow, and closeout truth."
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 59 closeout term in docs/phase-59-closeout-evaluation.md: AegisOps control-plane records remain authoritative"

missing_child_repo="${workdir}/missing-child"
copy_valid_repo "${missing_child_repo}"
remove_doc_text "${missing_child_repo}" \
  '| #1258 | Phase 59.6 Add stale/conflicting evidence AI fixtures | Closed. `control-plane/tests/fixtures/phase59/stale-conflicting-evidence-ai-fixtures.json` and `control-plane/tests/test_phase59_6_stale_conflicting_evidence_fixtures.py` force uncertainty and review-needed posture for stale, conflicting, uncited, outdated, or mismatched evidence. |'
assert_fails_with \
  "${missing_child_repo}" \
  "Missing required Phase 59 closeout term in docs/phase-59-closeout-evaluation.md: | #1258 | Phase 59.6 Add stale/conflicting evidence AI fixtures | Closed."

missing_prompt_evidence_repo="${workdir}/missing-prompt-evidence"
copy_valid_repo "${missing_prompt_evidence_repo}"
remove_doc_text "${missing_prompt_evidence_repo}" \
  "Prompt-pressure fixtures reject approval, execution, reconciliation, closure, detector activation, source-truth creation, citation suppression, uncertainty suppression, disallowed tool access, unregistered tool access, policy bypass, scope expansion, record-family expansion, secrets, and workstation-local path leakage."
assert_fails_with \
  "${missing_prompt_evidence_repo}" \
  "Missing required Phase 59 closeout term in docs/phase-59-closeout-evaluation.md: Prompt-pressure fixtures reject approval"

missing_trace_queue_evidence_repo="${workdir}/missing-trace-queue-evidence"
copy_valid_repo "${missing_trace_queue_evidence_repo}"
remove_doc_text "${missing_trace_queue_evidence_repo}" \
  'Trace review queue tests reject missing registered agent/tool/citation anchors, keep `read_only` true, keep `authoritative_workflow_truth` false, surface accepted/rejected/corrected states as review context only, and keep trace links subordinate to reviewed records.'
assert_fails_with \
  "${missing_trace_queue_evidence_repo}" \
  "Missing required Phase 59 closeout term in docs/phase-59-closeout-evaluation.md: Trace review queue tests reject missing registered agent/tool/citation anchors"

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/^- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1260 --config <supervisor-config-path>`: .*?\n//m' \
  "${missing_issue_lint_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  "Missing required Phase 59 closeout term in docs/phase-59-closeout-evaluation.md: node <codex-supervisor-root>/dist/index.js issue-lint 1260 --config <supervisor-config-path>"

missing_phase60_handoff_repo="${workdir}/missing-phase60-handoff"
copy_valid_repo "${missing_phase60_handoff_repo}"
remove_doc_text "${missing_phase60_handoff_repo}" \
  "Phase 60 can consume the Phase 59 governance foundation as a prerequisite for daily AI operations."
assert_fails_with \
  "${missing_phase60_handoff_repo}" \
  "Missing required Phase 59 closeout term in docs/phase-59-closeout-evaluation.md: Phase 60 can consume the Phase 59 governance foundation as a prerequisite for daily AI operations."

phase60_overclaim_repo="${workdir}/phase60-overclaim"
copy_valid_repo "${phase60_overclaim_repo}"
printf '%s\n' "Phase 60 daily AI operations are complete" >>"${phase60_overclaim_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${phase60_overclaim_repo}" \
  "Forbidden Phase 59 closeout evaluation claim: Phase 60 daily AI operations are complete"

commercial_overclaim_repo="${workdir}/commercial-overclaim"
copy_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "Phase 59 proves commercial replacement readiness" >>"${commercial_overclaim_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${commercial_overclaim_repo}" \
  "Forbidden Phase 59 closeout evaluation claim: Phase 59 proves commercial replacement readiness"

ai_approval_repo="${workdir}/ai-approval"
copy_valid_repo "${ai_approval_repo}"
printf '%s\n' "AI may approve actions" >>"${ai_approval_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${ai_approval_repo}" \
  "Forbidden Phase 59 closeout evaluation claim: AI may approve actions"

trace_truth_repo="${workdir}/trace-truth"
copy_valid_repo "${trace_truth_repo}"
printf '%s\n' "Trace state is workflow truth" >>"${trace_truth_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${trace_truth_repo}" \
  "Forbidden Phase 59 closeout evaluation claim: Trace state is workflow truth"

stale_truth_repo="${workdir}/stale-truth"
copy_valid_repo "${stale_truth_repo}"
printf '%s\n' "Stale evidence is current truth" >>"${stale_truth_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${stale_truth_repo}" \
  "Forbidden Phase 59 closeout evaluation claim: Stale evidence is current truth"

missing_citation_repo="${workdir}/missing-citation"
copy_valid_repo "${missing_citation_repo}"
printf '%s\n' "Missing citations may be hidden" >>"${missing_citation_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${missing_citation_repo}" \
  "Forbidden Phase 59 closeout evaluation claim: Missing citations may be hidden"

disabled_ai_block_repo="${workdir}/disabled-ai-block"
copy_valid_repo "${disabled_ai_block_repo}"
printf '%s\n' "Disabled AI may block case review" >>"${disabled_ai_block_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${disabled_ai_block_repo}" \
  "Forbidden Phase 59 closeout evaluation claim: Disabled AI may block case review"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 59 closeout evaluation: workstation-local absolute path detected"

absolute_path_windows_backslash_repo="${workdir}/absolute-path-windows-backslash"
copy_valid_repo "${absolute_path_windows_backslash_repo}"
windows_drive="C:"
windows_home_dir="Users"
printf 'Run %s\\%s\\example\\Dev\\codex-supervisor\\dist\\index.js.\n' "${windows_drive}" "${windows_home_dir}" >>"${absolute_path_windows_backslash_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_windows_backslash_repo}" \
  "Forbidden Phase 59 closeout evaluation: workstation-local absolute path detected"

absolute_path_windows_slash_repo="${workdir}/absolute-path-windows-slash"
copy_valid_repo "${absolute_path_windows_slash_repo}"
windows_home_slash="${windows_drive}/${windows_home_dir}/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${windows_home_slash}" >>"${absolute_path_windows_slash_repo}/docs/phase-59-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_windows_slash_repo}" \
  "Forbidden Phase 59 closeout evaluation: workstation-local absolute path detected"

echo "Phase 59 closeout verifier rejects missing evidence, authority expansion, overclaims, and local paths."
