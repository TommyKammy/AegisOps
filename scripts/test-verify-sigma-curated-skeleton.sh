#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-sigma-curated-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_curated_readme() {
  local target="$1"
  local content="$2"

  mkdir -p "${target}/sigma/curated"
  printf '%s\n' "${content}" > "${target}/sigma/curated/README.md"
}

assert_passes() {
  local target="$1"
  if ! "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"
  if "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi
  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

passing_repo="${workdir}/passing"
create_repo "${passing_repo}"
write_curated_readme \
  "${passing_repo}" \
"# Sigma Curated Directory

Purpose: reviewed Sigma rules approved for AegisOps onboarding.
Status: placeholder only; no active Sigma detection rules are committed here yet.
Rule onboarding requires future review and explicit approval before any real rule content is added."
assert_passes "${passing_repo}"

missing_marker_repo="${workdir}/missing-marker"
create_repo "${missing_marker_repo}"
write_curated_readme \
  "${missing_marker_repo}" \
"# Sigma Curated Directory

Purpose: reviewed Sigma rules approved for AegisOps onboarding."
assert_fails_with \
  "${missing_marker_repo}" \
  "Missing required sigma curated marker text: Status: placeholder only; no active Sigma detection rules are committed here yet."

unexpected_file_repo="${workdir}/unexpected-file"
create_repo "${unexpected_file_repo}"
write_curated_readme \
  "${unexpected_file_repo}" \
"# Sigma Curated Directory

Purpose: reviewed Sigma rules approved for AegisOps onboarding.
Status: placeholder only; no active Sigma detection rules are committed here yet.
Rule onboarding requires future review and explicit approval before any real rule content is added."
printf 'title: real-rule\n' > "${unexpected_file_repo}/sigma/curated/rule.yml"
assert_fails_with \
  "${unexpected_file_repo}" \
  "Unexpected placeholder content in ${unexpected_file_repo}/sigma/curated; only ${unexpected_file_repo}/sigma/curated/README.md is allowed."

unexpected_directory_repo="${workdir}/unexpected-directory"
create_repo "${unexpected_directory_repo}"
write_curated_readme \
  "${unexpected_directory_repo}" \
"# Sigma Curated Directory

Purpose: reviewed Sigma rules approved for AegisOps onboarding.
Status: placeholder only; no active Sigma detection rules are committed here yet.
Rule onboarding requires future review and explicit approval before any real rule content is added."
mkdir -p "${unexpected_directory_repo}/sigma/curated/pending"
assert_fails_with \
  "${unexpected_directory_repo}" \
  "Unexpected placeholder content in ${unexpected_directory_repo}/sigma/curated; only ${unexpected_directory_repo}/sigma/curated/README.md is allowed."

echo "verify-sigma-curated-skeleton tests passed"
