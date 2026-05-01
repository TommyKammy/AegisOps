#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-closeout-evaluation.sh"

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
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-52-closeout-evaluation.md" "${target}/docs/phase-52-closeout-evaluation.md"
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
  "Missing Phase 52 closeout evaluation: docs/phase-52-closeout-evaluation.md"

missing_readme_link_repo="${workdir}/missing-readme-link"
copy_valid_repo "${missing_readme_link_repo}"
perl -0pi -e 's/\[Phase 52\.10 closeout evaluation\]\(docs\/phase-52-closeout-evaluation\.md\)/Phase 52.10 closeout evaluation/g' \
  "${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "Missing README Phase 52.10 closeout link: [Phase 52.10 closeout evaluation](docs/phase-52-closeout-evaluation.md)"

missing_child_issue_lint_repo="${workdir}/missing-child-issue-lint"
copy_valid_repo "${missing_child_issue_lint_repo}"
perl -0pi -e 's/node <codex-supervisor-root>\/dist\/index\.js issue-lint 1068 --config <supervisor-config-path>\n//' \
  "${missing_child_issue_lint_repo}/docs/phase-52-closeout-evaluation.md"
assert_fails_with \
  "${missing_child_issue_lint_repo}" \
  "Missing required closeout term in docs/phase-52-closeout-evaluation.md: node <codex-supervisor-root>/dist/index.js issue-lint 1068 --config <supervisor-config-path>"

missing_phase53_blockers_repo="${workdir}/missing-phase53-blockers"
copy_valid_repo "${missing_phase53_blockers_repo}"
perl -0pi -e 's/Explicit blockers for Phase 53 are live Wazuh profile implementation, reviewed Wazuh version pinning, trusted Wazuh secret references, Wazuh volume separation, Wazuh ingest route binding, and replacement of fixture-backed `init`, `up`, and `doctor` checks with live profile-backed behavior\.//' \
  "${missing_phase53_blockers_repo}/docs/phase-52-closeout-evaluation.md"
assert_fails_with \
  "${missing_phase53_blockers_repo}" \
  'Missing required closeout term in docs/phase-52-closeout-evaluation.md: Explicit blockers for Phase 53 are live Wazuh profile implementation, reviewed Wazuh version pinning, trusted Wazuh secret references, Wazuh volume separation, Wazuh ingest route binding, and replacement of fixture-backed `init`, `up`, and `doctor` checks with live profile-backed behavior.'

missing_phase54_blockers_repo="${workdir}/missing-phase54-blockers"
copy_valid_repo "${missing_phase54_blockers_repo}"
perl -0pi -e 's/Explicit blockers for Phase 54 are live Shuffle profile implementation, reviewed Shuffle version pinning, trusted Shuffle API and callback secret references, Shuffle workflow-catalog custody, callback route binding, volume separation, and replacement of fixture-backed `seed-demo` or delegated-execution checks with live profile-backed behavior\.//' \
  "${missing_phase54_blockers_repo}/docs/phase-52-closeout-evaluation.md"
assert_fails_with \
  "${missing_phase54_blockers_repo}" \
  'Missing required closeout term in docs/phase-52-closeout-evaluation.md: Explicit blockers for Phase 54 are live Shuffle profile implementation, reviewed Shuffle version pinning, trusted Shuffle API and callback secret references, Shuffle workflow-catalog custody, callback route binding, volume separation, and replacement of fixture-backed `seed-demo` or delegated-execution checks with live profile-backed behavior.'

ga_overclaim_repo="${workdir}/ga-overclaim"
copy_valid_repo "${ga_overclaim_repo}"
printf '%s\n' "Phase 52 proves GA readiness" >>"${ga_overclaim_repo}/docs/phase-52-closeout-evaluation.md"
assert_fails_with \
  "${ga_overclaim_repo}" \
  "Forbidden Phase 52 closeout evaluation claim: Phase 52 proves GA readiness"

wazuh_truth_repo="${workdir}/wazuh-truth"
copy_valid_repo "${wazuh_truth_repo}"
printf '%s\n' "Wazuh state is AegisOps workflow truth" >>"${wazuh_truth_repo}/docs/phase-52-closeout-evaluation.md"
assert_fails_with \
  "${wazuh_truth_repo}" \
  "Forbidden Phase 52 closeout evaluation claim: Wazuh state is AegisOps workflow truth"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-52-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 52 closeout evaluation: workstation-local absolute path detected"

echo "Phase 52 closeout evaluation verifier tests passed."
