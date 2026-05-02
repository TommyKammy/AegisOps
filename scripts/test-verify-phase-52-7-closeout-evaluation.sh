#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-7-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-52-7-closeout-evaluation.md" "${target}/docs/phase-52-7-closeout-evaluation.md"
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
  "Missing Phase 52.7 closeout evaluation: docs/phase-52-7-closeout-evaluation.md"

missing_readme_link_repo="${workdir}/missing-readme-link"
copy_valid_repo "${missing_readme_link_repo}"
perl -0pi -e 's/\[Phase 52\.7 closeout evaluation\]\(docs\/phase-52-7-closeout-evaluation\.md\)/Phase 52.7 closeout evaluation/g' \
  "${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "Missing README Phase 52.7 closeout link: [Phase 52.7 closeout evaluation](docs/phase-52-7-closeout-evaluation.md)"

missing_compatibility_repo="${workdir}/missing-retained-compatibility"
copy_valid_repo "${missing_compatibility_repo}"
perl -0pi -e 's/Legacy compatibility behavior is preserved, not removed\.//' \
  "${missing_compatibility_repo}/docs/phase-52-7-closeout-evaluation.md"
assert_fails_with \
  "${missing_compatibility_repo}" \
  "Missing required Phase 52.7 closeout term in docs/phase-52-7-closeout-evaluation.md: Legacy compatibility behavior is preserved, not removed."

phase53_overclaim_repo="${workdir}/phase53-overclaim"
copy_valid_repo "${phase53_overclaim_repo}"
printf '%s\n' "Phase 53 Wazuh product profile work is completed" >>"${phase53_overclaim_repo}/docs/phase-52-7-closeout-evaluation.md"
assert_fails_with \
  "${phase53_overclaim_repo}" \
  "Forbidden Phase 52.7 closeout evaluation claim: Phase 53 Wazuh product profile work is completed"

missing_root_counts_repo="${workdir}/missing-root-counts"
copy_valid_repo "${missing_root_counts_repo}"
perl -0pi -e 's/\| Phase 52\.6 accepted baseline before Phase 52\.7 physical layout migration, under `control-plane\/aegisops_control_plane\/` \| 37 \|\n//' \
  "${missing_root_counts_repo}/docs/phase-52-7-closeout-evaluation.md"
assert_fails_with \
  "${missing_root_counts_repo}" \
  'Missing required Phase 52.7 closeout term in docs/phase-52-7-closeout-evaluation.md: | Phase 52.6 accepted baseline before Phase 52.7 physical layout migration, under `control-plane/aegisops_control_plane/` | 37 |'

missing_namespace_paths_repo="${workdir}/missing-namespace-paths"
copy_valid_repo "${missing_namespace_paths_repo}"
perl -0pi -e 's/\| Implementation package path \| `control-plane\/aegisops_control_plane\/` \| `control-plane\/aegisops\/control_plane\/` \|\n//' \
  "${missing_namespace_paths_repo}/docs/phase-52-7-closeout-evaluation.md"
assert_fails_with \
  "${missing_namespace_paths_repo}" \
  'Missing required Phase 52.7 closeout term in docs/phase-52-7-closeout-evaluation.md: | Implementation package path | `control-plane/aegisops_control_plane/` | `control-plane/aegisops/control_plane/` |'

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-52-7-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 52.7 closeout evaluation: workstation-local absolute path detected"

echo "Phase 52.7 closeout evaluation verifier tests passed."
