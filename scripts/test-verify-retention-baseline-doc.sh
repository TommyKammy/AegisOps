#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-retention-baseline-doc.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
}

write_doc() {
  local target="$1"
  local content="$2"

  printf '%s\n' "${content}" >"${target}/docs/retention-evidence-and-replay-readiness-baseline.md"
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
write_doc "${valid_repo}" '# AegisOps Retention, Evidence Lifecycle, and Replay Readiness Baseline

## 1. Purpose

This document defines the baseline retention classes, evidence lifecycle assumptions, and replay readiness expectations for AegisOps-owned records.

## 2. Retention Classes

| Record family | Baseline |
| ---- | ---- |
| `Raw Event` | Baseline placeholder |
| `Normalized Event` | Baseline placeholder |
| `Finding` | Baseline placeholder |
| `Alert` | Baseline placeholder |
| `Evidence` | Baseline placeholder |
| `Approval Decision` | Baseline placeholder |
| `Action Execution` | Baseline placeholder |

## 3. Replay Dataset and Restore Readiness Expectations

Replay-capable datasets must be retained long enough to support parser validation, rule validation, and targeted historical reprocessing for approved investigations and recovery exercises.

Restore readiness must assume application-aware restore procedures for OpenSearch, PostgreSQL, and future platform-owned control records rather than treating hypervisor snapshots as the primary recovery model.

## 4. Evidence Lifecycle and Legal-Hold Baseline

Evidence retention must preserve chain-of-custody context, source provenance, review references, and legal-hold status long enough to support audit, investigation, and post-incident review.

Legal hold must suspend ordinary expiration for specifically scoped evidence and related approval or execution records until the hold is explicitly released through approved process.

## 5. Lifecycle Policy Constraints

This baseline defines policy-level hot, warm, cold, or rollover expectations only. It does not introduce live ILM policies, shard counts, index templates, storage tier automation, or production retention settings in this phase.

## 6. Baseline Alignment Notes

The document remains a baseline artifact only.'
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing retention baseline document:"

missing_phrase_repo="${workdir}/missing-phrase"
create_repo "${missing_phrase_repo}"
write_doc "${missing_phrase_repo}" '# AegisOps Retention, Evidence Lifecycle, and Replay Readiness Baseline

## 1. Purpose

This document defines the baseline retention classes, evidence lifecycle assumptions, and replay readiness expectations for AegisOps-owned records.

## 2. Retention Classes

| Record family | Baseline |
| ---- | ---- |
| `Raw Event` | Baseline placeholder |
| `Normalized Event` | Baseline placeholder |
| `Finding` | Baseline placeholder |
| `Alert` | Baseline placeholder |
| `Evidence` | Baseline placeholder |
| `Approval Decision` | Baseline placeholder |
| `Action Execution` | Baseline placeholder |

## 3. Replay Dataset and Restore Readiness Expectations

Restore readiness must assume application-aware restore procedures for OpenSearch, PostgreSQL, and future platform-owned control records rather than treating hypervisor snapshots as the primary recovery model.

## 4. Evidence Lifecycle and Legal-Hold Baseline

Evidence retention must preserve chain-of-custody context, source provenance, review references, and legal-hold status long enough to support audit, investigation, and post-incident review.

Legal hold must suspend ordinary expiration for specifically scoped evidence and related approval or execution records until the hold is explicitly released through approved process.

## 5. Lifecycle Policy Constraints

This baseline defines policy-level hot, warm, cold, or rollover expectations only. It does not introduce live ILM policies, shard counts, index templates, storage tier automation, or production retention settings in this phase.

## 6. Baseline Alignment Notes

The document remains a baseline artifact only.'
assert_fails_with "${missing_phrase_repo}" "Replay-capable datasets must be retained long enough to support parser validation, rule validation, and targeted historical reprocessing for approved investigations and recovery exercises."

echo "verify-retention-baseline-doc tests passed"
