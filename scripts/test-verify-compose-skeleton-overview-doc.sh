#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-compose-skeleton-overview-doc.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
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

  write_file "${target}" "docs/compose-skeleton-overview.md" "# AegisOps Compose Skeleton Overview

This document explains the purpose and limits of the tracked Docker Compose skeletons in this repository.

It consolidates the approved scaffolding intent for contributors and reviewers before runtime implementation work expands.

## 1. Purpose

The compose skeletons exist to provide placeholder-safe scaffolding for approved AegisOps component boundaries.

They are not production-ready deployment definitions.

They do not introduce new architecture, deployment behavior, or runtime defaults.

## 2. What The Skeletons Are For

- Reserving the expected component directories and Compose project names for AegisOps assets.
- Showing placeholder-safe service boundaries for OpenSearch, n8n, PostgreSQL, proxy, and ingest roles.
- Keeping contributor examples aligned to the approved documentation baseline before implementation details are finalized.

Treat the skeletons as contributor scaffolding, not as a complete deployment design.

## 3. What Remains Out of Scope

- Live secrets, active environment files, and production credential material.
- Final host paths, certificate rollout, ingress publication, and production exposure decisions beyond documented policy.
- Complete service hardening, scaling, clustering, backup automation, restore automation, or environment-specific deployment tuning.

Do not treat placeholder paths, placeholder environment values, or placeholder profiles as approved production settings.

## 4. Contributor Guidance

When updating a compose skeleton, preserve the current placeholder-safe posture unless a separately approved issue or ADR changes the baseline.

Use the skeletons to keep names, roles, and directory ownership aligned while deferring runtime-specific implementation details to the approved baseline and policy documents.

## 5. Reference Documents

- \`docs/requirements-baseline.md\`
- \`docs/contributor-naming-guide.md\`
- \`docs/network-exposure-and-access-path-policy.md\`
- \`docs/storage-layout-and-mount-policy.md\`
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
assert_fails_with "${missing_doc_repo}" "Missing compose skeleton overview document"

missing_reference_repo="${workdir}/missing-reference"
create_repo "${missing_reference_repo}"
write_valid_doc "${missing_reference_repo}"
write_file "${missing_reference_repo}" "docs/compose-skeleton-overview.md" "# AegisOps Compose Skeleton Overview

This document explains the purpose and limits of the tracked Docker Compose skeletons in this repository.

It consolidates the approved scaffolding intent for contributors and reviewers before runtime implementation work expands.

## 1. Purpose

The compose skeletons exist to provide placeholder-safe scaffolding for approved AegisOps component boundaries.

They are not production-ready deployment definitions.

They do not introduce new architecture, deployment behavior, or runtime defaults.

## 2. What The Skeletons Are For

- Reserving the expected component directories and Compose project names for AegisOps assets.
- Showing placeholder-safe service boundaries for OpenSearch, n8n, PostgreSQL, proxy, and ingest roles.
- Keeping contributor examples aligned to the approved documentation baseline before implementation details are finalized.

Treat the skeletons as contributor scaffolding, not as a complete deployment design.

## 3. What Remains Out of Scope

- Live secrets, active environment files, and production credential material.
- Final host paths, certificate rollout, ingress publication, and production exposure decisions beyond documented policy.
- Complete service hardening, scaling, clustering, backup automation, restore automation, or environment-specific deployment tuning.

Do not treat placeholder paths, placeholder environment values, or placeholder profiles as approved production settings.

## 4. Contributor Guidance

When updating a compose skeleton, preserve the current placeholder-safe posture unless a separately approved issue or ADR changes the baseline.

Use the skeletons to keep names, roles, and directory ownership aligned while deferring runtime-specific implementation details to the approved baseline and policy documents.

## 5. Reference Documents

- \`docs/requirements-baseline.md\`
- \`docs/contributor-naming-guide.md\`
- \`docs/network-exposure-and-access-path-policy.md\`
- \`docs/repository-structure-baseline.md\`"
commit_fixture "${missing_reference_repo}"
assert_fails_with "${missing_reference_repo}" "Missing compose skeleton overview reference"

echo "Compose skeleton overview verifier tests passed."
