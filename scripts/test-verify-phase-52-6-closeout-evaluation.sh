#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-6-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-52-6-closeout-evaluation.md" "${target}/docs/phase-52-6-closeout-evaluation.md"
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
  "Missing Phase 52.6 closeout evaluation: docs/phase-52-6-closeout-evaluation.md"

missing_readme_link_repo="${workdir}/missing-readme-link"
copy_valid_repo "${missing_readme_link_repo}"
perl -0pi -e 's/\[Phase 52\.6 closeout evaluation\]\(docs\/phase-52-6-closeout-evaluation\.md\)/Phase 52.6 closeout evaluation/g' \
  "${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "Missing README Phase 52.6 closeout link: [Phase 52.6 closeout evaluation](docs/phase-52-6-closeout-evaluation.md)"

missing_blocker_repo="${workdir}/missing-retained-blocker"
copy_valid_repo "${missing_blocker_repo}"
perl -0pi -e 's/The retained compatibility blocker is `service\.py`[^.]*\.//' \
  "${missing_blocker_repo}/docs/phase-52-6-closeout-evaluation.md"
assert_fails_with \
  "${missing_blocker_repo}" \
  'Missing required Phase 52.6 closeout term in docs/phase-52-6-closeout-evaluation.md: The retained compatibility blocker is `service.py`'

missing_phase29_status_repo="${workdir}/missing-phase29-status"
copy_valid_repo "${missing_phase29_status_repo}"
perl -0pi -e 's/Phase29 root filename status: no direct root Python filename begins with `phaseNN` or `phaseNN_` after Phase 52\.6\.6\.//' \
  "${missing_phase29_status_repo}/docs/phase-52-6-closeout-evaluation.md"
assert_fails_with \
  "${missing_phase29_status_repo}" \
  'Missing required Phase 52.6 closeout term in docs/phase-52-6-closeout-evaluation.md: Phase29 root filename status: no direct root Python filename begins with `phaseNN` or `phaseNN_` after Phase 52.6.6.'

wazuh_overclaim_repo="${workdir}/wazuh-overclaim"
copy_valid_repo "${wazuh_overclaim_repo}"
printf '%s\n' "The Wazuh product profile is complete" >>"${wazuh_overclaim_repo}/docs/phase-52-6-closeout-evaluation.md"
assert_fails_with \
  "${wazuh_overclaim_repo}" \
  "Forbidden Phase 52.6 closeout evaluation claim: The Wazuh product profile is complete"

shuffle_overclaim_repo="${workdir}/shuffle-overclaim"
copy_valid_repo "${shuffle_overclaim_repo}"
printf '%s\n' "The Shuffle product profile work is complete" >>"${shuffle_overclaim_repo}/docs/phase-52-6-closeout-evaluation.md"
assert_fails_with \
  "${shuffle_overclaim_repo}" \
  "Forbidden Phase 52.6 closeout evaluation claim: The Shuffle product profile work is complete"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-52-6-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 52.6 closeout evaluation: workstation-local absolute path detected"

echo "Phase 52.6 closeout evaluation verifier tests passed."
