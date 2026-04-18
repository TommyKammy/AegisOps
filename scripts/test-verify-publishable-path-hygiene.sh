#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-publishable-path-hygiene.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"
  shift

  mkdir -p "${target}"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"

  while (($#)); do
    local path="$1"
    local content="$2"
    shift 2

    mkdir -p "${target}/$(dirname "${path}")"
    printf '%s\n' "${content}" > "${target}/${path}"
    git -C "${target}" add "${path}"
  done

  git -C "${target}" commit -q -m "fixture"
}

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
  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

clean_repo="${workdir}/clean"
create_repo \
  "${clean_repo}" \
  "README.md" "# Clean fixture" \
  "docs/phase-25.md" "Reviewed roadmap reference: ObsidianVault/Dev/AegisOps/Plan&Roadmap/Revised Phase23-29 Epic Roadmap.md" \
  "control-plane/tests/test_docs.py" "EXPECTED_PATH = 'docs/phase-25.md'"
assert_passes "${clean_repo}"

allowlisted_repo="${workdir}/allowlisted"
create_repo \
  "${allowlisted_repo}" \
  "README.md" "# Allowlisted fixture" \
  "control-plane/tests/test_publishable_path_hygiene.py" "PATH = '/Users/jp.infra/tmp'  # publishable-path-hygiene: allowlist fixture" \
  "docs/phase-25.md" "Reviewed roadmap reference stays vault-relative."
assert_passes "${allowlisted_repo}"

failing_repo="${workdir}/failing"
create_repo \
  "${failing_repo}" \
  "README.md" "# Failing fixture" \
  "docs/phase-25.md" "Leaked path: /Users/jp.infra/Library/Mobile Documents/com~apple~CloudDocs/ObsidianVault/Dev/AegisOps/Plan&Roadmap/Revised Phase23-29 Epic Roadmap.md" \
  "control-plane/tests/test_docs.py" "EXPECTED_PATH = 'docs/phase-25.md'"
assert_fails_with "${failing_repo}" "docs/phase-25.md:1:"

echo "verify-publishable-path-hygiene tests passed"
