#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-opensearch-index-template-guidance.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/opensearch/index-templates"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_file() {
  local target="$1"
  local path="$2"
  local content="$3"

  printf '%s\n' "${content}" >"${target}/${path}"
  git -C "${target}" add "${path}"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
}

write_valid_doc() {
  local target="$1"

  write_file "${target}" "opensearch/index-templates/README.md" "# AegisOps OpenSearch Index Template Placeholders

This document explains the purpose and current limits of the tracked OpenSearch index template placeholders.

## 1. Purpose

These files exist to reserve the approved OpenSearch log index-template names and directory ownership for AegisOps contributors.

They are placeholders only and are not production-ready index templates.

## 2. Placeholder Scope

- Keep the approved \`aegisops-logs-<family>-*\` naming pattern visible in version control.
- Reserve a stable location for future index-template work under the approved \`opensearch/\` repository boundary.
- Make it clear that the current JSON files are scaffolding for contributors and reviewers, not finished OpenSearch content.

## 3. What Remains Out of Scope

Do not treat the current files as approved mappings, settings, shard plans, lifecycle policies, or ingestion contracts.

- Production field mappings and analyzers.
- Index lifecycle management, rollover, and retention behavior.
- Environment-specific shard counts, replica counts, or performance tuning.
- Template priorities, aliases, or pipeline attachments beyond the current placeholder state.

## 4. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline.

When updating these placeholders, keep them descriptive-only and aligned to the approved naming baseline until production template requirements are formally documented.

## 5. Reference Documents

- \`docs/requirements-baseline.md\`
- \`docs/contributor-naming-guide.md\`
- \`docs/repository-structure-baseline.md\`"
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

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_valid_doc "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing OpenSearch index template guidance document"

missing_reference_repo="${workdir}/missing-reference"
create_repo "${missing_reference_repo}"
write_file "${missing_reference_repo}" "opensearch/index-templates/README.md" "# AegisOps OpenSearch Index Template Placeholders

This document explains the purpose and current limits of the tracked OpenSearch index template placeholders.

## 1. Purpose

These files exist to reserve the approved OpenSearch log index-template names and directory ownership for AegisOps contributors.

They are placeholders only and are not production-ready index templates.

## 2. Placeholder Scope

- Keep the approved \`aegisops-logs-<family>-*\` naming pattern visible in version control.
- Reserve a stable location for future index-template work under the approved \`opensearch/\` repository boundary.
- Make it clear that the current JSON files are scaffolding for contributors and reviewers, not finished OpenSearch content.

## 3. What Remains Out of Scope

Do not treat the current files as approved mappings, settings, shard plans, lifecycle policies, or ingestion contracts.

- Production field mappings and analyzers.
- Index lifecycle management, rollover, and retention behavior.
- Environment-specific shard counts, replica counts, or performance tuning.
- Template priorities, aliases, or pipeline attachments beyond the current placeholder state.

## 4. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline.

When updating these placeholders, keep them descriptive-only and aligned to the approved naming baseline until production template requirements are formally documented.

## 5. Reference Documents

- \`docs/requirements-baseline.md\`
- \`docs/repository-structure-baseline.md\`"
commit_fixture "${missing_reference_repo}"
assert_fails_with "${missing_reference_repo}" "Missing OpenSearch index template guidance reference"

echo "OpenSearch index template guidance verifier tests passed."
