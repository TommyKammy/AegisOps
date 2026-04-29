#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-49-production-rbac-auth-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_contract_doc() {
  local target="$1"
  local content="$2"

  mkdir -p "${target}/docs"
  printf '%s\n' "${content}" >"${target}/docs/phase-49-production-rbac-auth-hardening-contract.md"
}

create_valid_repo() {
  local target="$1"

  write_contract_doc "${target}" '# Phase 49.1 Production RBAC and Auth Hardening Contract

## 1. Purpose

This contract fixes the production RBAC and authentication hardening posture for later Phase 49 implementation work without changing runtime behavior in this issue.

AegisOps control-plane records remain authoritative for approval decisions, action requests, action executions, evidence linkage, lifecycle state, and reconciliation truth.

## 2. Production Role Contract

| Role | Allowed authority | Forbidden shortcut |
| ---- | ---- | ---- |
| `analyst` | Review assigned alerts, cases, evidence, observations, leads, recommendations, advisory context, and reconciliation status; create or update investigation notes and submit approval-bound action requests inside assigned scope. | Approve approval-sensitive actions, execute actions directly, administer platform identity, or override reconciliation truth. |
| `approver` | Review approval-bound action requests, inspect the authoritative evidence and scope bindings, approve or reject delegated actions within the assigned action class, and record the approval decision. | Approve requests without an attributable requester, approve their own approval-sensitive request, execute actions as the approving human, or use assistant/ticket/browser context as approval authority. |
| `platform_admin` | Operate platform configuration, secret delivery paths, identity-provider wiring, service accounts, readiness checks, and recovery procedures. | Use administrative access as a response-action approval path, mutate workflow truth without the control-plane record chain, or grant broad role overlap without a reviewed exception. |

## 3. Permission Contract

Authorization must be evaluated by the backend control-plane boundary for every protected read, every write-capable operator action, every approval decision, every action execution delegation, and every reconciliation closeout.

Browser route gating, UI menu visibility, reverse-proxy access control, external-ticket assignment, assistant output, endpoint evidence, network evidence, downstream receipts, and optional extension state are subordinate controls or context only.

## 4. Trusted Identity Boundary

The trusted identity boundary is a reviewed IdP session normalized by the approved reverse-proxy path and bound to backend-reviewed claims before the control plane admits protected access.

Raw `X-Forwarded-*`, `Forwarded`, `Host`, `X-User`, `X-Email`, tenant, proto, role, or scope headers must not be trusted unless the approved proxy has authenticated, normalized, and sealed the boundary before backend evaluation.

Placeholder credentials, sample tokens, unsigned tokens, TODO values, empty secrets, stale secret reads, and locally guessed identity values must be rejected.

## 5. Fail-Closed Conditions

If the authenticated subject, reviewed provider, role assignment, action scope, tenant or environment scope, approval binding, requester identity, or executor identity is missing, stale, ambiguous, malformed, or contradictory, the protected path must fail closed.

Fail-closed means the backend rejects the protected operation, leaves authoritative workflow records unchanged, records or surfaces the reason for operator follow-up, and does not substitute guessed context.

## 6. Subordinate Context and Forbidden Trust Paths

Subordinate sources must never become authority for identity, role, approval, execution, reconciliation, case lifecycle, evidence custody, or commercial-readiness state.

## 7. Validation Expectations

Protected-surface validation must include negative cases for missing identity-provider binding, unreviewed provider boundary, missing reviewed role claim, ambiguous role overlap, raw forwarded-header identity, placeholder credentials, and stale or unreadable secret-backed identity context.

Failure-path validation must prove durable state remains clean after rejected, forbidden, failed, or restore-failure paths, not only that an exception or error was returned.

## 8. Scope Boundaries

This contract does not implement runtime RBAC, change approval or action execution policy, add audit export, retention, observability, reporting, multi-tenant, MSSP, HA, or production write behavior, or expand `service.py` responsibilities beyond the ADR-0003 closeout ceiling.

## 9. Verification Commands

Run `bash scripts/verify-phase-49-production-rbac-auth-contract.sh`.
Run `bash scripts/test-verify-phase-49-production-rbac-auth-contract.sh`.
Run `node <codex-supervisor-root>/dist/index.js issue-lint 934 --config <supervisor-config-path>`.'
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

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 49.1 production RBAC/auth contract"

missing_forwarded_header_repo="${workdir}/missing-forwarded-header"
create_valid_repo "${missing_forwarded_header_repo}"
perl -0pi -e 's/Raw `X-Forwarded-\*`, `Forwarded`, `Host`, `X-User`, `X-Email`, tenant, proto, role, or scope headers must not be trusted unless the approved proxy has authenticated, normalized, and sealed the boundary before backend evaluation\.//g' \
  "${missing_forwarded_header_repo}/docs/phase-49-production-rbac-auth-hardening-contract.md"
assert_fails_with \
  "${missing_forwarded_header_repo}" \
  'Missing Phase 49.1 production RBAC/auth contract statement: Raw `X-Forwarded-*`, `Forwarded`, `Host`, `X-User`, `X-Email`, tenant, proto, role, or scope headers must not be trusted unless the approved proxy has authenticated, normalized, and sealed the boundary before backend evaluation.'

missing_fail_closed_repo="${workdir}/missing-fail-closed"
create_valid_repo "${missing_fail_closed_repo}"
perl -0pi -e 's/If the authenticated subject, reviewed provider, role assignment, action scope, tenant or environment scope, approval binding, requester identity, or executor identity is missing, stale, ambiguous, malformed, or contradictory, the protected path must fail closed\.//g' \
  "${missing_fail_closed_repo}/docs/phase-49-production-rbac-auth-hardening-contract.md"
assert_fails_with \
  "${missing_fail_closed_repo}" \
  "Missing Phase 49.1 production RBAC/auth contract statement: If the authenticated subject, reviewed provider, role assignment, action scope, tenant or environment scope, approval binding, requester identity, or executor identity is missing, stale, ambiguous, malformed, or contradictory, the protected path must fail closed."

missing_state_clean_repo="${workdir}/missing-state-clean"
create_valid_repo "${missing_state_clean_repo}"
perl -0pi -e 's/Failure-path validation must prove durable state remains clean after rejected, forbidden, failed, or restore-failure paths, not only that an exception or error was returned\.//g' \
  "${missing_state_clean_repo}/docs/phase-49-production-rbac-auth-hardening-contract.md"
assert_fails_with \
  "${missing_state_clean_repo}" \
  "Missing Phase 49.1 production RBAC/auth contract statement: Failure-path validation must prove durable state remains clean after rejected, forbidden, failed, or restore-failure paths, not only that an exception or error was returned."

echo "verify-phase-49-production-rbac-auth-contract tests passed"
