#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-sigma-guidance-doc.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/sigma"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/sigma/README.md"
  git -C "${target}" add sigma/README.md
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
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
write_doc "${valid_repo}" '# AegisOps Sigma Content Guidance

## Purpose

This document records the approved governance model for Sigma content tracked in this repository.

The baseline source of truth remains docs/requirements-baseline.md.

## Directory Roles

### `curated/`

This directory is reserved for reviewed Sigma rules that are approved for future AegisOps onboarding.

A rule belongs in `curated/` when it has passed content review and is retained as an approved candidate for future platform onboarding.

### `suppressed/`

This directory is reserved for documented suppression decisions for Sigma content that should remain excluded from onboarding.

An entry belongs in `suppressed/` when the decision to exclude or defer Sigma content must be preserved with documented rationale, review, and approval context.

## Review Expectations

Any future addition under either directory must remain reviewable, attributable, and explicitly approved before placeholder-only status is removed.

## Validation Expectations

Contributors must validate that directory purpose, review state, and supporting documentation remain clear before merging changes.

## Scope Boundary

This document defines repository content governance only. It does not activate detections, create suppression behavior, or change runtime execution in OpenSearch, Sigma tooling, or n8n.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Sigma guidance document:"

missing_validation_repo="${workdir}/missing-validation"
create_repo "${missing_validation_repo}"
write_doc "${missing_validation_repo}" '# AegisOps Sigma Content Guidance

## Purpose

This document records the approved governance model for Sigma content tracked in this repository.

The baseline source of truth remains docs/requirements-baseline.md.

## Directory Roles

### `curated/`

This directory is reserved for reviewed Sigma rules that are approved for future AegisOps onboarding.

A rule belongs in `curated/` when it has passed content review and is retained as an approved candidate for future platform onboarding.

### `suppressed/`

This directory is reserved for documented suppression decisions for Sigma content that should remain excluded from onboarding.

An entry belongs in `suppressed/` when the decision to exclude or defer Sigma content must be preserved with documented rationale, review, and approval context.

## Review Expectations

Any future addition under either directory must remain reviewable, attributable, and explicitly approved before placeholder-only status is removed.

## Scope Boundary

This document defines repository content governance only. It does not activate detections, create suppression behavior, or change runtime execution in OpenSearch, Sigma tooling, or n8n.'
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing heading in Sigma guidance document: ## Validation Expectations"

echo "verify-sigma-guidance-doc tests passed"
