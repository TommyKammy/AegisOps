#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-61-8-closeout-evaluation.sh"

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

  if ! grep -Fiq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-61-closeout-evaluation.md" "${target}/docs/phase-61-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-61-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

url_path_repo="${workdir}/url-path"
copy_valid_repo "${url_path_repo}"
users_segment="Users"
home_segment="home"
printf '%s\n' \
  "Reference URL: https://example.com/${home_segment}/docs/phase-61-closeout" \
  "Reference URL: https://example.com/C:/${users_segment}/docs/phase-61-closeout" \
  "Reference URL: https://example.com/search?artifact=/${users_segment}/example/Dev/codex-supervisor/dist/index.js" \
  >>"${url_path_repo}/docs/phase-61-closeout-evaluation.md"
assert_passes "${url_path_repo}"

relative_home_repo="${workdir}/relative-home"
copy_valid_repo "${relative_home_repo}"
printf '%s\n' "Relative fixture path: ./${home_segment}/example/Dev/codex-supervisor/dist/index.js" \
  >>"${relative_home_repo}/docs/phase-61-closeout-evaluation.md"
assert_passes "${relative_home_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 61 closeout evaluation: docs/phase-61-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 61\.8 closeout evaluation\]\(docs\/phase-61-closeout-evaluation\.md\)[^\n]*\n/- Phase 61.8 closeout evaluation\\n/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 61.8 closeout evaluation](docs/phase-61-closeout-evaluation.md)"

missing_readme_product_positioning_repo="${workdir}/missing-readme-product-positioning"
copy_valid_repo "${missing_readme_product_positioning_repo}"
perl -0pi -e 's/The Phase 61\.8 closeout evaluation is defined by the \[Phase 61\.8 closeout evaluation\]\(docs\/phase-61-closeout-evaluation\.md\)\./The Phase 61.8 closeout evaluation is defined by the Phase 61.8 closeout evaluation./' \
  "${missing_readme_product_positioning_repo}/README.md"
assert_fails_with \
  "${missing_readme_product_positioning_repo}" \
  "Missing README Product positioning reference: The Phase 61.8 closeout evaluation is defined by the [Phase 61.8 closeout evaluation](docs/phase-61-closeout-evaluation.md)."

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
remove_doc_text "${missing_authority_repo}" \
  "AegisOps control-plane records remain authoritative for alert, case, evidence, detector lifecycle, false-positive review, suppression proposal, source-health record, search-result navigation, approval, action request, execution receipt, reconciliation, audit event, limitation, release, gate, and closeout truth."
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 61 closeout term in docs/phase-61-closeout-evaluation.md: AegisOps control-plane records remain authoritative"

missing_child_repo="${workdir}/missing-child"
copy_valid_repo "${missing_child_repo}"
remove_doc_text "${missing_child_repo}" \
  "| #1296 | Phase 61.8 Phase 61 closeout evaluation | Open until this document and focused closeout verifier land. |"
assert_fails_with \
  "${missing_child_repo}" \
  "Missing required Phase 61 closeout term in docs/phase-61-closeout-evaluation.md: | #1296 | Phase 61.8 Phase 61 closeout evaluation | Open until this document and focused closeout verifier land. |"

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1296 --config <supervisor-config-path>`.*\n//m' \
  "${missing_issue_lint_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  'Missing required Phase 61 closeout term in docs/phase-61-closeout-evaluation.md: `node <codex-supervisor-root>/dist/index.js issue-lint 1296 --config <supervisor-config-path>`'

missing_path_hygiene_repo="${workdir}/missing-path-hygiene"
copy_valid_repo "${missing_path_hygiene_repo}"
remove_doc_text "${missing_path_hygiene_repo}" \
  "Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output."
assert_fails_with \
  "${missing_path_hygiene_repo}" \
  "Missing required Phase 61 closeout term in docs/phase-61-closeout-evaluation.md: Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output."

phase62_overclaim_repo="${workdir}/phase62-overclaim"
copy_valid_repo "${phase62_overclaim_repo}"
printf '%s\n' "Phase 62 SOAR breadth is complete" >>"${phase62_overclaim_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${phase62_overclaim_repo}" \
  "Forbidden Phase 61 closeout evaluation claim: Phase 62 SOAR breadth is complete"

commercial_overclaim_repo="${workdir}/commercial-overclaim"
copy_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "AegisOps is a commercial replacement for every SIEM/SOAR capability" >>"${commercial_overclaim_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${commercial_overclaim_repo}" \
  "Forbidden Phase 61 closeout evaluation claim: AegisOps is a commercial replacement for every SIEM/SOAR capability"

raw_siem_overclaim_repo="${workdir}/raw-siem-overclaim"
copy_valid_repo "${raw_siem_overclaim_repo}"
printf '%s\n' "Raw SIEM search replacement is complete" >>"${raw_siem_overclaim_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${raw_siem_overclaim_repo}" \
  "Forbidden Phase 61 closeout evaluation claim: Raw SIEM search replacement is complete"

source_truth_repo="${workdir}/source-truth"
copy_valid_repo "${source_truth_repo}"
printf '%s\n' "Source-native status is AegisOps truth" >>"${source_truth_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${source_truth_repo}" \
  "Forbidden Phase 61 closeout evaluation claim: Source-native status is AegisOps truth"

silent_suppression_repo="${workdir}/silent-suppression"
copy_valid_repo "${silent_suppression_repo}"
printf '%s\n' "Silent suppression is allowed" >>"${silent_suppression_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${silent_suppression_repo}" \
  "Forbidden Phase 61 closeout evaluation claim: Silent suppression is allowed"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
printf 'Run /%s/example/Dev/codex-supervisor/dist/index.js.\n' "Users" >>"${absolute_path_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 61 closeout evaluation: workstation-local absolute path detected"

file_url_absolute_path_repo="${workdir}/file-url-absolute-path"
copy_valid_repo "${file_url_absolute_path_repo}"
printf 'Run file:///%s/example/Dev/codex-supervisor/dist/index.js.\n' "Users" \
  >>"${file_url_absolute_path_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${file_url_absolute_path_repo}" \
  "Forbidden Phase 61 closeout evaluation: workstation-local absolute path detected"

absolute_path_windows_backslash_repo="${workdir}/absolute-path-windows-backslash"
copy_valid_repo "${absolute_path_windows_backslash_repo}"
windows_drive="C:"
windows_sep="\\"
windows_path="${windows_drive}${windows_sep}Users${windows_sep}example${windows_sep}Dev${windows_sep}codex-supervisor${windows_sep}dist${windows_sep}index.js"
printf '%s\n' "Run ${windows_path}." >>"${absolute_path_windows_backslash_repo}/docs/phase-61-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_windows_backslash_repo}" \
  "Forbidden Phase 61 closeout evaluation: workstation-local absolute path detected"

echo "Phase 61 closeout evaluation verifier tests passed."
