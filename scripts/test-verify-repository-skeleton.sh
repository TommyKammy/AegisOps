#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-repository-skeleton.sh"

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
    shift

    mkdir -p "${target}/$(dirname "${path}")"
    if [[ "${path}" == */ ]]; then
      mkdir -p "${target}/${path%/}"
      : > "${target}/${path%/}/.keep"
      git -C "${target}" add "${path%/}/.keep"
    else
      : > "${target}/${path}"
      git -C "${target}" add "${path}"
    fi
  done

  git -C "${target}" commit -q -m "fixture"
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

approved_repo="${workdir}/approved-license"
create_repo \
  "${approved_repo}" \
  ".codex-supervisor/README.md" \
  ".env.sample" \
  ".github/workflows/ci.yml" \
  ".gitignore" \
  "LICENSE.txt" \
  "README.md" \
  "apps/operator-ui/README.md" \
  "config/" \
  "control-plane/" \
  "docs/" \
  "ingest/" \
  "n8n/" \
  "opensearch/" \
  "package-lock.json" \
  "package.json" \
  "playwright.config.ts" \
  "postgres/" \
  "proxy/" \
  "scripts/" \
  "sigma/"
assert_passes "${approved_repo}"

tracked_supervisor_journal_repo="${workdir}/tracked-supervisor-journal"
create_repo \
  "${tracked_supervisor_journal_repo}" \
  ".codex-supervisor/README.md" \
  ".codex-supervisor/issues/94/issue-journal.md" \
  ".env.sample" \
  ".github/workflows/ci.yml" \
  ".gitignore" \
  "LICENSE.txt" \
  "README.md" \
  "apps/operator-ui/README.md" \
  "config/" \
  "control-plane/" \
  "docs/" \
  "ingest/" \
  "n8n/" \
  "opensearch/" \
  "package-lock.json" \
  "package.json" \
  "playwright.config.ts" \
  "postgres/" \
  "proxy/" \
  "scripts/" \
  "sigma/"
assert_fails_with "${tracked_supervisor_journal_repo}" "Tracked supervisor-local journal is not allowed"

unexpected_hidden_repo="${workdir}/unexpected-hidden-dir"
create_repo \
  "${unexpected_hidden_repo}" \
  ".cache/" \
  ".codex-supervisor/README.md" \
  ".env.sample" \
  ".github/workflows/ci.yml" \
  ".gitignore" \
  "LICENSE.txt" \
  "README.md" \
  "apps/operator-ui/README.md" \
  "config/" \
  "control-plane/" \
  "docs/" \
  "ingest/" \
  "n8n/" \
  "opensearch/" \
  "package-lock.json" \
  "package.json" \
  "playwright.config.ts" \
  "postgres/" \
  "proxy/" \
  "scripts/" \
  "sigma/"
assert_fails_with "${unexpected_hidden_repo}" ".cache"

echo "verify-repository-skeleton tests passed"
