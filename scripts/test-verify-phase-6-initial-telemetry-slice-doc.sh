#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-6-initial-telemetry-slice-doc.sh"

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

  printf '%s\n' "${doc_content}" >"${target}/docs/phase-6-initial-telemetry-slice.md"
  git -C "${target}" add docs/phase-6-initial-telemetry-slice.md
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
write_doc "${valid_repo}" '# AegisOps Phase 6 Initial Telemetry Slice

## 1. Purpose

This document selects the single initial telemetry family and first detection use cases for the Phase 6 validated slice.

## 2. Selected Initial Telemetry Family

The selected initial telemetry family for the Phase 6 slice is Windows security and endpoint telemetry.

Phase 6 starts with one telemetry family only.

## 3. Selected Initial Detection Use Cases

The initial use cases below are intentionally limited to single-event detections that can be reviewed during business hours and exercised through replay.

The Phase 6 slice is limited to these three initial detection use cases:

1. Privileged group membership change
2. Audit log cleared
3. New local user created

Each selected use case can be exercised with replayable Windows event samples and handled through read-only analyst workflow steps before any approval-bound response exists.

## 4. Selection Rationale

Windows telemetry is the best first proof of the Phase 5 contracts because it exercises actor identity, host identity, provenance, timestamp semantics, and Sigma-compatible single-event detection patterns in one family.

Network telemetry is deferred because volume, directionality, and product variance would broaden parser and tuning scope too early.

Linux telemetry is deferred because initial source heterogeneity would widen normalization and replay coverage before the first vertical slice is proven.

SaaS audit telemetry is deferred because provider-specific action semantics would force early cross-provider narrowing inside a family that is still too broad for the first validated slice.

## 5. Scope Guardrails

No additional telemetry families, correlation logic, threshold-based analytics, response automation, or after-hours operating promises are included in this slice.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Phase 6 initial telemetry slice document:"

too_many_repo="${workdir}/too-many"
create_repo "${too_many_repo}"
write_doc "${too_many_repo}" '# AegisOps Phase 6 Initial Telemetry Slice

## 1. Purpose

This document selects the single initial telemetry family and first detection use cases for the Phase 6 validated slice.

## 2. Selected Initial Telemetry Family

The selected initial telemetry family for the Phase 6 slice is Windows security and endpoint telemetry.

Phase 6 starts with one telemetry family only.

## 3. Selected Initial Detection Use Cases

The initial use cases below are intentionally limited to single-event detections that can be reviewed during business hours and exercised through replay.

The Phase 6 slice is limited to these three initial detection use cases:

1. Privileged group membership change
2. Audit log cleared
3. New local user created
4. Extra use case

Each selected use case can be exercised with replayable Windows event samples and handled through read-only analyst workflow steps before any approval-bound response exists.

## 4. Selection Rationale

Windows telemetry is the best first proof of the Phase 5 contracts because it exercises actor identity, host identity, provenance, timestamp semantics, and Sigma-compatible single-event detection patterns in one family.

Network telemetry is deferred because volume, directionality, and product variance would broaden parser and tuning scope too early.

Linux telemetry is deferred because initial source heterogeneity would widen normalization and replay coverage before the first vertical slice is proven.

SaaS audit telemetry is deferred because provider-specific action semantics would force early cross-provider narrowing inside a family that is still too broad for the first validated slice.

## 5. Scope Guardrails

No additional telemetry families, correlation logic, threshold-based analytics, response automation, or after-hours operating promises are included in this slice.'
commit_fixture "${too_many_repo}"
assert_fails_with "${too_many_repo}" "Expected exactly three numbered initial detection use cases, found 4."

echo "Phase 6 initial telemetry slice verifier tests passed."
