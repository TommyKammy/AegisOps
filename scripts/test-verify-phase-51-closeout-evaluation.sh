#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-51-closeout-evaluation.sh"

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
  cp "${repo_root}/docs/phase-51-closeout-evaluation.md" "${target}/docs/phase-51-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 51 closeout evaluation: docs/phase-51-closeout-evaluation.md"

missing_phase52_guard_repo="${workdir}/missing-phase52-guard"
copy_valid_repo "${missing_phase52_guard_repo}"
perl -0pi -e 's/Do not materialize Phase 52 while repo-owned graph or preflight state still reports Phase 51 as `materialized_open`, stale, missing, or otherwise unreconciled\.//' \
  "${missing_phase52_guard_repo}/docs/phase-51-closeout-evaluation.md"
assert_fails_with \
  "${missing_phase52_guard_repo}" \
  'Missing required closeout term in docs/phase-51-closeout-evaluation.md: Do not materialize Phase 52 while repo-owned graph or preflight state still reports Phase 51 as `materialized_open`, stale, missing, or otherwise unreconciled.'

ga_overclaim_repo="${workdir}/ga-overclaim"
copy_valid_repo "${ga_overclaim_repo}"
printf '%s\n' "AegisOps is already GA" >>"${ga_overclaim_repo}/docs/phase-51-closeout-evaluation.md"
assert_fails_with \
  "${ga_overclaim_repo}" \
  "Forbidden Phase 51 closeout evaluation claim: AegisOps is already GA"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
mac_home_prefix="/""Users/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${mac_home_prefix}" >>"${absolute_path_repo}/docs/phase-51-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 51 closeout evaluation: workstation-local absolute path detected"

linux_home_path_repo="${workdir}/linux-home-path"
copy_valid_repo "${linux_home_path_repo}"
linux_home_prefix="/""home/example"
printf 'Run %s/Dev/codex-supervisor/dist/index.js.\n' "${linux_home_prefix}" >>"${linux_home_path_repo}/docs/phase-51-closeout-evaluation.md"
assert_fails_with \
  "${linux_home_path_repo}" \
  "Forbidden Phase 51 closeout evaluation: workstation-local absolute path detected"

windows_slash_path_repo="${workdir}/windows-slash-path"
copy_valid_repo "${windows_slash_path_repo}"
windows_slash_path="C:""/""Users/example/repo/file.md"
printf 'Run %s.\n' "${windows_slash_path}" >>"${windows_slash_path_repo}/docs/phase-51-closeout-evaluation.md"
assert_fails_with \
  "${windows_slash_path_repo}" \
  "Forbidden Phase 51 closeout evaluation: workstation-local absolute path detected"

windows_backslash_path_repo="${workdir}/windows-backslash-path"
copy_valid_repo "${windows_backslash_path_repo}"
windows_backslash_path="$(printf 'C:%bUsers%bexample%brepo%bfile.md' '\\' '\\' '\\' '\\')"
printf 'Run %s.\n' "${windows_backslash_path}" >>"${windows_backslash_path_repo}/docs/phase-51-closeout-evaluation.md"
assert_fails_with \
  "${windows_backslash_path_repo}" \
  "Forbidden Phase 51 closeout evaluation: workstation-local absolute path detected"

echo "Phase 51 closeout evaluation verifier tests passed."
