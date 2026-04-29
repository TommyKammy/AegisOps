# Phase 49.1 Production RBAC and Auth Hardening Contract

- **Status**: Accepted
- **Date**: 2026-04-29
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/auth-baseline.md`, `docs/architecture.md`, `docs/response-action-safety-model.md`, `docs/control-plane-state-model.md`, `docs/adr/0003-phase-49-service-decomposition-boundaries.md`
- **Related Issue**: #934

## 1. Purpose

This contract fixes the production RBAC and authentication hardening posture for later Phase 49 implementation work without changing runtime behavior in this issue.

It turns the existing auth baseline into a commercial-readiness contract for protected operator and backend surfaces while preserving the AegisOps authority model.

AegisOps control-plane records remain authoritative for approval decisions, action requests, action executions, evidence linkage, lifecycle state, and reconciliation truth.

This contract is design and validation only. It does not create live users, integrate an IdP, mint secrets, change approval behavior, or introduce production writes.

## 2. Production Role Contract

Production implementation must start from these least-privilege roles. A later issue may split a role into narrower implementation claims, but it must not weaken the forbidden shortcuts or make subordinate context authoritative.

| Role | Allowed authority | Forbidden shortcut |
| ---- | ---- | ---- |
| `analyst` | Review assigned alerts, cases, evidence, observations, leads, recommendations, advisory context, and reconciliation status; create or update investigation notes and submit approval-bound action requests inside assigned scope. | Approve approval-sensitive actions, execute actions directly, administer platform identity, or override reconciliation truth. |
| `approver` | Review approval-bound action requests, inspect the authoritative evidence and scope bindings, approve or reject delegated actions within the assigned action class, and record the approval decision. | Approve requests without an attributable requester, approve their own approval-sensitive request, execute actions as the approving human, or use assistant/ticket/browser context as approval authority. |
| `platform_admin` | Operate platform configuration, secret delivery paths, identity-provider wiring, service accounts, readiness checks, and recovery procedures. | Use administrative access as a response-action approval path, mutate workflow truth without the control-plane record chain, or grant broad role overlap without a reviewed exception. |

Role assignment must be attributable to one reviewed human or machine identity record. Shared interactive administrator accounts, anonymous operator identities, mailbox-backed users, and human-owned automation tokens remain forbidden shortcuts.

## 3. Permission Contract

Authorization must be evaluated by the backend control-plane boundary for every protected read, every write-capable operator action, every approval decision, every action execution delegation, and every reconciliation closeout.

The backend authorization decision must bind at least:

- reviewed identity-provider boundary;
- authenticated provider subject;
- reviewed AegisOps identity;
- reviewed role claim;
- action class or protected surface;
- authoritative record identifier;
- tenant or environment scope when that scope exists; and
- requester, approver, and executor separation when the operation touches approval or execution.

Browser route gating, UI menu visibility, reverse-proxy access control, external-ticket assignment, assistant output, endpoint evidence, network evidence, downstream receipts, and optional extension state are subordinate controls or context only.

If browser and backend authorization disagree, the backend denial wins and the browser must preserve the denial explicitly instead of rendering guessed or cached protected content.

## 4. Trusted Identity Boundary

The trusted identity boundary is a reviewed IdP session normalized by the approved reverse-proxy path and bound to backend-reviewed claims before the control plane admits protected access.

The approved boundary must make these signals available to backend authorization:

- reviewed identity-provider identifier;
- authenticated provider subject;
- reviewed AegisOps identity string;
- reviewed role or role set;
- session freshness or expiry status;
- scope binding for the protected record or environment; and
- provenance that the signal crossed the approved proxy boundary.

Raw `X-Forwarded-*`, `Forwarded`, `Host`, `X-User`, `X-Email`, tenant, proto, role, or scope headers must not be trusted unless the approved proxy has authenticated, normalized, and sealed the boundary before backend evaluation.

Placeholder credentials, sample tokens, unsigned tokens, TODO values, empty secrets, stale secret reads, and locally guessed identity values must be rejected.

Machine identity for automation must remain separate from human operator identity. A human approval record may authorize a bounded action, but execution must still occur under a reviewed machine or executor identity that can be reconciled back to the approved action scope.

## 5. Fail-Closed Conditions

If the authenticated subject, reviewed provider, role assignment, action scope, tenant or environment scope, approval binding, requester identity, or executor identity is missing, stale, ambiguous, malformed, or contradictory, the protected path must fail closed.

Fail-closed means the backend rejects the protected operation, leaves authoritative workflow records unchanged, records or surfaces the reason for operator follow-up, and does not substitute guessed context.

Specific fail-closed examples:

- missing reviewed IdP binding rejects protected operator access as unauthorized;
- authenticated session without a reviewed role claim rejects protected access as forbidden or invalid-session;
- conflicting `analyst` and `approver` claims on an approval-sensitive self-approval path rejects the approval;
- raw forwarded identity headers without a sealed proxy boundary reject the request;
- external ticket assignee or browser route state cannot authorize a protected backend read;
- assistant recommendation, endpoint evidence, network evidence, or downstream receipt cannot approve, execute, or close a workflow record;
- stale or unreadable secret-backed identity context blocks the protected operation instead of falling back to plaintext or a cached sample value; and
- restore, export, backup, or readiness paths that cannot prove a snapshot-consistent identity and record chain must reject or escalate instead of presenting a mixed-state success.

Rejected, forbidden, failed, or restore-failure paths must not leave orphan records, partial durable writes, half-restored state, or authority-shaped derived summaries behind.

## 6. Subordinate Context and Forbidden Trust Paths

Subordinate sources must never become authority for identity, role, approval, execution, reconciliation, case lifecycle, evidence custody, or commercial-readiness state.

The forbidden authority sources are:

- raw browser headers or client-supplied identity fields;
- browser route state, menu visibility, cached shell state, local storage, or optional extension state;
- external tickets, ticket assignees, ticket comments, ticket closure, or support workflow state;
- assistant output, model output, recommendations, summaries, or advisory lineage;
- ML, endpoint evidence, network evidence, OpenSearch documents, Wazuh local state, Shuffle state, n8n state, receipts, or downstream run metadata;
- naming conventions, path shape, nearby metadata, comments, labels, badges, counters, or operator-facing projection text; and
- placeholder credentials, sample tokens, unsigned tokens, TODO values, empty secrets, or stale secret reads.

Those sources may support explanation, triage, or reconciliation only after they are explicitly bound to the authoritative AegisOps control-plane record chain.

## 7. Validation Expectations

Protected-surface validation must include negative cases for missing identity-provider binding, unreviewed provider boundary, missing reviewed role claim, ambiguous role overlap, raw forwarded-header identity, placeholder credentials, and stale or unreadable secret-backed identity context.

Implementation issues must anchor tests at the enforcement boundary that actually authorizes or rejects the protected operation. Setup-only tests are not sufficient when later authorization, provenance, scope, or durable-state checks decide the outcome.

Failure-path validation must prove durable state remains clean after rejected, forbidden, failed, or restore-failure paths, not only that an exception or error was returned.

Validation for backup, restore, export, readiness, and detail aggregation must prove snapshot-consistent reads or explicit rejection of mixed-snapshot results.

Validation for one logical change that writes multiple records must prove all-or-nothing persistence and must not hold database transactions open across network hops, queued jobs, adapter dispatch, or remote waits.

## 8. Scope Boundaries

This contract does not implement runtime RBAC, change approval or action execution policy, add audit export, retention, observability, reporting, multi-tenant, MSSP, HA, or production write behavior, or expand `service.py` responsibilities beyond the ADR-0003 closeout ceiling.

Later Phase 49 implementation may add code and tests for this posture, but it must preserve:

- backend-authoritative approval and action governance;
- the existing public control-plane authority boundary;
- separation between requester, approver, and executor identity;
- the subordinate posture of tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, and optional extension state; and
- fail-closed behavior when prerequisite identity, scope, provenance, or durable-state signals are not trustworthy.

## 9. Verification Commands

Run `bash scripts/verify-phase-49-production-rbac-auth-contract.sh`.

Run `bash scripts/test-verify-phase-49-production-rbac-auth-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 934 --config <supervisor-config-path>`.
