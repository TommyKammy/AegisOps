#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-sigma-to-opensearch-translation-strategy-doc.sh"

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

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/sigma-to-opensearch-translation-strategy.md"
  git -C "${target}" add docs/sigma-to-opensearch-translation-strategy.md
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
write_doc "${valid_repo}" '# AegisOps Sigma-to-OpenSearch Translation Strategy

## 1. Purpose

This document defines the approved Sigma-to-OpenSearch translation strategy for the AegisOps baseline.

It makes the supported Sigma subset, required metadata, deferred features, and OpenSearch-native fallback path explicit before runtime detector implementation begins.

This strategy defines translation scope and review boundaries only. It does not claim full Sigma parity and does not approve automatic detector generation or production activation.

## 2. Baseline Translation Boundary

AegisOps supports only single-rule, single-event Sigma detections whose logic can be translated into reviewable OpenSearch detector content without changing the rule'\''s meaning.

## 3. Supported Sigma Subset for the Approved Baseline

The approved baseline supports selection-based field matching, boolean condition composition using `and`, `or`, and `not`, and stable comparisons on normalized fields that have documented source coverage.

| Status | Sigma capability handling |
| ---- | ---- |
| Supported for baseline translation | Simple single-event selections on normalized fields; boolean combinations that preserve straight-through detector meaning |

## 4. Required Rule Metadata and Source Prerequisites

Each rule proposed for translation must declare rule identity, owner, severity, purpose, ATT&CK mapping, normalized field dependencies, source-family prerequisites, and known false-positive considerations.

## 5. Unsupported and Deferred Sigma Feature Matrix

The baseline does not support Sigma correlation, aggregations, temporal counting semantics, cross-index joins, multi-source dependencies, or field logic that depends on unsupported modifiers without a separate approved design.

| Status | Sigma capability handling |
| ---- | ---- |
| Deferred pending separate design | Correlation blocks; aggregation or threshold semantics; temporal sequences; multi-source joins |
| Forbidden for straight-through translation | Content that requires hidden enrichment assumptions, undocumented field remapping, or runtime behavior outside approved OpenSearch detector responsibilities |

## 6. OpenSearch-Native Fallback Path

When a detection requirement cannot be translated safely from the approved Sigma subset, the detection must remain OpenSearch-native and carry explicit documentation that Sigma is not the source of truth for that rule.

OpenSearch-native fallback content must still preserve owner, purpose, source prerequisites, field dependencies, validation evidence, and false-positive notes so review standards remain consistent.

## 7. Baseline Alignment Notes

This strategy remains aligned with `docs/requirements-baseline.md`, `docs/source-onboarding-contract.md`, and `docs/secops-domain-model.md`.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Sigma-to-OpenSearch translation strategy document:"

missing_fallback_repo="${workdir}/missing-fallback"
create_repo "${missing_fallback_repo}"
write_doc "${missing_fallback_repo}" '# AegisOps Sigma-to-OpenSearch Translation Strategy

## 1. Purpose

This document defines the approved Sigma-to-OpenSearch translation strategy for the AegisOps baseline.

It makes the supported Sigma subset, required metadata, deferred features, and OpenSearch-native fallback path explicit before runtime detector implementation begins.

This strategy defines translation scope and review boundaries only. It does not claim full Sigma parity and does not approve automatic detector generation or production activation.

## 2. Baseline Translation Boundary

AegisOps supports only single-rule, single-event Sigma detections whose logic can be translated into reviewable OpenSearch detector content without changing the rule'\''s meaning.

## 3. Supported Sigma Subset for the Approved Baseline

The approved baseline supports selection-based field matching, boolean condition composition using `and`, `or`, and `not`, and stable comparisons on normalized fields that have documented source coverage.

| Status | Sigma capability handling |
| ---- | ---- |
| Supported for baseline translation | Simple single-event selections on normalized fields; boolean combinations that preserve straight-through detector meaning |

## 4. Required Rule Metadata and Source Prerequisites

Each rule proposed for translation must declare rule identity, owner, severity, purpose, ATT&CK mapping, normalized field dependencies, source-family prerequisites, and known false-positive considerations.

## 5. Unsupported and Deferred Sigma Feature Matrix

The baseline does not support Sigma correlation, aggregations, temporal counting semantics, cross-index joins, multi-source dependencies, or field logic that depends on unsupported modifiers without a separate approved design.

| Status | Sigma capability handling |
| ---- | ---- |
| Deferred pending separate design | Correlation blocks; aggregation or threshold semantics; temporal sequences; multi-source joins |
| Forbidden for straight-through translation | Content that requires hidden enrichment assumptions, undocumented field remapping, or runtime behavior outside approved OpenSearch detector responsibilities |

## 6. OpenSearch-Native Fallback Path

OpenSearch-native fallback content must still preserve owner, purpose, source prerequisites, field dependencies, validation evidence, and false-positive notes so review standards remain consistent.

## 7. Baseline Alignment Notes

This strategy remains aligned with `docs/requirements-baseline.md`, `docs/source-onboarding-contract.md`, and `docs/secops-domain-model.md`.'
commit_fixture "${missing_fallback_repo}"
assert_fails_with "${missing_fallback_repo}" "Missing Sigma-to-OpenSearch strategy statement: When a detection requirement cannot be translated safely from the approved Sigma subset, the detection must remain OpenSearch-native and carry explicit documentation that Sigma is not the source of truth for that rule."

echo "verify-sigma-to-opensearch-translation-strategy-doc tests passed"
