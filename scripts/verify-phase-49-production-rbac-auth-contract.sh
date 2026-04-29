#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-49-production-rbac-auth-hardening-contract.md"

required_headings=(
  "# Phase 49.1 Production RBAC and Auth Hardening Contract"
  "## 1. Purpose"
  "## 2. Production Role Contract"
  "## 3. Permission Contract"
  "## 4. Trusted Identity Boundary"
  "## 5. Fail-Closed Conditions"
  "## 6. Subordinate Context and Forbidden Trust Paths"
  "## 7. Validation Expectations"
  "## 8. Scope Boundaries"
  "## 9. Verification Commands"
)

required_phrases=(
  "This contract fixes the production RBAC and authentication hardening posture for later Phase 49 implementation work without changing runtime behavior in this issue."
  "AegisOps control-plane records remain authoritative for approval decisions, action requests, action executions, evidence linkage, lifecycle state, and reconciliation truth."
  '| `analyst` | Review assigned alerts, cases, evidence, observations, leads, recommendations, advisory context, and reconciliation status; create or update investigation notes and submit approval-bound action requests inside assigned scope. | Approve approval-sensitive actions, execute actions directly, administer platform identity, or override reconciliation truth. |'
  '| `approver` | Review approval-bound action requests, inspect the authoritative evidence and scope bindings, approve or reject delegated actions within the assigned action class, and record the approval decision. | Approve requests without an attributable requester, approve their own approval-sensitive request, execute actions as the approving human, or use assistant/ticket/browser context as approval authority. |'
  '| `platform_admin` | Operate platform configuration, secret delivery paths, identity-provider wiring, service accounts, readiness checks, and recovery procedures. | Use administrative access as a response-action approval path, mutate workflow truth without the control-plane record chain, or grant broad role overlap without a reviewed exception. |'
  "Authorization must be evaluated by the backend control-plane boundary for every protected read, every write-capable operator action, every approval decision, every action execution delegation, and every reconciliation closeout."
  "Browser route gating, UI menu visibility, reverse-proxy access control, external-ticket assignment, assistant output, endpoint evidence, network evidence, downstream receipts, and optional extension state are subordinate controls or context only."
  "The trusted identity boundary is a reviewed IdP session normalized by the approved reverse-proxy path and bound to backend-reviewed claims before the control plane admits protected access."
  'Raw `X-Forwarded-*`, `Forwarded`, `Host`, `X-User`, `X-Email`, tenant, proto, role, or scope headers must not be trusted unless the approved proxy has authenticated, normalized, and sealed the boundary before backend evaluation.'
  "Placeholder credentials, sample tokens, unsigned tokens, TODO values, empty secrets, stale secret reads, and locally guessed identity values must be rejected."
  "If the authenticated subject, reviewed provider, role assignment, action scope, tenant or environment scope, approval binding, requester identity, or executor identity is missing, stale, ambiguous, malformed, or contradictory, the protected path must fail closed."
  "Fail-closed means the backend rejects the protected operation, leaves authoritative workflow records unchanged, records or surfaces the reason for operator follow-up, and does not substitute guessed context."
  "Subordinate sources must never become authority for identity, role, approval, execution, reconciliation, case lifecycle, evidence custody, or commercial-readiness state."
  "Protected-surface validation must include negative cases for missing identity-provider binding, unreviewed provider boundary, missing reviewed role claim, ambiguous role overlap, raw forwarded-header identity, placeholder credentials, and stale or unreadable secret-backed identity context."
  "Failure-path validation must prove durable state remains clean after rejected, forbidden, failed, or restore-failure paths, not only that an exception or error was returned."
  'This contract does not implement runtime RBAC, change approval or action execution policy, add audit export, retention, observability, reporting, multi-tenant, MSSP, HA, or production write behavior, or expand `service.py` responsibilities beyond the ADR-0003 closeout ceiling.'
  'Run `bash scripts/verify-phase-49-production-rbac-auth-contract.sh`.'
  'Run `bash scripts/test-verify-phase-49-production-rbac-auth-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 934 --config <supervisor-config-path>`.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 49.1 production RBAC/auth contract: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 49.1 production RBAC/auth contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fxq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 49.1 production RBAC/auth contract statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Phase 49.1 production RBAC/auth contract is present and preserves backend authority, fail-closed identity handling, and forbidden trust paths."
