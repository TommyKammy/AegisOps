#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-49-service-decomposition-adr.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_phase49_adr() {
  local target="$1"
  local content="$2"

  mkdir -p "${target}/docs/adr"
  printf '%s\n' "${content}" >"${target}/docs/adr/0003-phase-49-service-decomposition-boundaries.md"
}

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' "# Thresholds" "docs/maintainability-hotspot-baseline.txt" >"${target}/docs/maintainability-decomposition-thresholds.md"

  write_phase49_adr "${target}" '# ADR-0003: Phase 49 Service Decomposition Boundaries and Migration Order

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #918, #919, #920, #921, #922, #923, #924, #925
- **Supersedes**: N/A
- **Superseded By**: N/A

## 1. Context

AegisOpsControlPlaneService remains the public facade for Phase 49.0 behavior-preserving decomposition work.

The first implementation issue must not start before this ADR is merged.

## 2. Decision

We will preserve the existing public facade while extracting internal collaborators.

The target service boundaries are:
- Intake and triage boundary
- Case mutation and evidence linkage boundary
- Advisory and AI trace lifecycle boundary
- Action and reconciliation orchestration boundary
- Runtime, restore, and readiness diagnostics boundary

The migration order is:
1. #919 ADR and verification gate
2. #920 intake and triage extraction
3. #921 case mutation and evidence linkage extraction
4. #922 advisory and AI trace lifecycle extraction
5. #923 action and reconciliation orchestration extraction
6. #924 runtime, restore, and readiness diagnostics extraction
7. #925 hotspot baseline refresh and validation closeout

## 3. Decision Drivers

- maintainability
- auditability
- behavior preservation
- authority-boundary preservation

## 4. Options Considered

### Option A: Ordered behavior-preserving decomposition behind the existing facade

#### Description
Extract one internal boundary at a time while the facade remains stable.

#### Pros
- Keeps behavior stable.

#### Cons
- Requires strict sequencing.

### Option B: Rewrite the service boundary in one issue

#### Description
Replace the facade and collaborators together.

#### Pros
- Completes faster on paper.

#### Cons
- Broadens regression risk.

### Option C: Continue extending the hotspot in place

#### Description
Leave the current service concentration untouched.

#### Pros
- Avoids immediate extraction work.

#### Cons
- Ignores the governing hotspot contract.

## 5. Rationale

Option A is selected because it follows `docs/maintainability-decomposition-thresholds.md` while preserving runtime behavior.

## 6. Consequences

### Positive Consequences
- Child issues have fixed ownership boundaries.

### Negative Consequences
- The sequence cannot be parallelized safely.

### Neutral / Follow-up Consequences
- `docs/maintainability-hotspot-baseline.txt` is refreshed only after extraction lands.

## 7. Implementation Impact

Every extraction slice must keep the facade behavior-preserving and add focused regression coverage for its boundary.

## 8. Security Impact

This ADR does not change approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, secrets, or write-capable authority.

## 9. Rollback / Exit Strategy

Rollback removes this ADR and its verifier wiring before implementation extraction starts.

## 10. Validation

Run `bash scripts/verify-phase-49-service-decomposition-adr.sh`.
Run `bash scripts/test-verify-phase-49-service-decomposition-adr.sh`.
Run `node <codex-supervisor-root>/dist/index.js issue-lint 919 --config <supervisor-config-path>`.

## 11. Non-Goals

- No production code extraction is approved by this ADR.
- No commercial readiness capability is added.
- Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, and optional extension status remain subordinate context and do not become workflow truth.

## 12. Approval

- **Proposed By**: Codex for Issue #919
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-29'
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

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_adr_repo="${workdir}/missing-adr"
create_valid_repo "${missing_adr_repo}"
rm "${missing_adr_repo}/docs/adr/0003-phase-49-service-decomposition-boundaries.md"
assert_fails_with \
  "${missing_adr_repo}" \
  "Missing Phase 49 service decomposition ADR"

missing_boundary_repo="${workdir}/missing-boundary"
create_valid_repo "${missing_boundary_repo}"
perl -0pi -e 's/- Action and reconciliation orchestration boundary\n//' \
  "${missing_boundary_repo}/docs/adr/0003-phase-49-service-decomposition-boundaries.md"
assert_fails_with \
  "${missing_boundary_repo}" \
  "Missing Phase 49 service decomposition ADR statement: - Action and reconciliation orchestration boundary"

missing_order_repo="${workdir}/missing-order"
create_valid_repo "${missing_order_repo}"
perl -0pi -e 's/5\. #923 action and reconciliation orchestration extraction/5. #923 omitted orchestration extraction/' \
  "${missing_order_repo}/docs/adr/0003-phase-49-service-decomposition-boundaries.md"
assert_fails_with \
  "${missing_order_repo}" \
  "Missing Phase 49 service decomposition ADR statement: 5. #923 action and reconciliation orchestration extraction"

missing_authority_repo="${workdir}/missing-authority"
create_valid_repo "${missing_authority_repo}"
perl -0pi -e 's/Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, and optional extension status remain subordinate context and do not become workflow truth\.//g' \
  "${missing_authority_repo}/docs/adr/0003-phase-49-service-decomposition-boundaries.md"
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing Phase 49 service decomposition ADR statement: Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, and optional extension status remain subordinate context and do not become workflow truth."

echo "verify-phase-49-service-decomposition-adr tests passed"
