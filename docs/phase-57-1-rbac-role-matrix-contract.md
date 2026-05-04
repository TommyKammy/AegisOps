# Phase 57.1 RBAC Role Matrix Contract

- **Status**: Accepted
- **Date**: 2026-05-04
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-49-production-rbac-auth-hardening-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/phase-55-closeout-evaluation.md`, `docs/phase-56-closeout-evaluation.md`
- **Related Issues**: #1207, #1208

## 1. Purpose

This contract defines the minimum commercial RBAC role matrix before user, role, source, action policy, retention, audit export, and AI enablement administration expands.

The RBAC matrix defines access and policy posture only. It cannot rewrite historical workflow truth or make support or external users authoritative for approval, execution, reconciliation, audit, release, gate, or closeout truth.

## 2. Role Matrix

| Role | Workbench inspection | Investigation notes | Action request submission | Action approval decision | Platform administration | Support diagnostics | Audit export | External collaboration | Workflow authority override | Historical truth rewrite |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `platform_admin` | read-only | read-only | denied | denied | admin-only | denied | admin-only | denied | denied | denied |
| `analyst` | allowed | allowed | allowed | denied | denied | denied | denied | denied | denied | denied |
| `approver` | read-only | read-only | denied | allowed | denied | denied | denied | denied | denied | denied |
| `read_only_auditor` | read-only | read-only | denied | denied | denied | denied | read-only | denied | denied | denied |
| `support_operator` | read-only | read-only | denied | denied | denied | support-only | denied | denied | denied | denied |
| `external_collaborator` | read-only | read-only | denied | denied | denied | denied | denied | no-authority | denied | denied |

## 3. Required Behavior

The matrix covers allowed, denied, read-only, admin-only, support-only, and no-authority behavior.

Platform admin access is admin-only for configuration and audit-export posture; it is not approval, execution, reconciliation, closeout, release, or gate authority.

Analyst access can submit approval-bound action requests in assigned scope, but analyst access cannot approve approval-sensitive work or rewrite workflow truth.

Approver access can record reviewed approval decisions in assigned scope, but approver access cannot submit its own approval-bound request through role confusion or execute actions as the approving human.

Read-only auditor access can inspect reviewed workflow and audit surfaces, but it cannot write investigation notes, submit action requests, approve actions, operate support diagnostics, administer the platform, or rewrite historical truth.

Support operator access is support-only for customer-safe diagnostics and cannot receive workflow authority for approval, execution, reconciliation, audit, release, gate, or closeout truth.

External collaborator access is no-authority collaboration context and cannot receive workflow authority for approval, execution, reconciliation, audit, release, gate, or closeout truth.

## 4. Authority Boundary

Backend authorization remains the enforcement boundary for protected reads, write-capable operator actions, approval decisions, action execution delegation, reconciliation closeout, audit export, support diagnostics, and administration.

Browser route gating, UI menu visibility, role cache, support text, external collaborator context, ticket state, assistant output, downstream receipts, and operator-facing summaries are subordinate surfaces only.

If browser role cache and backend authorization disagree, the backend denial wins and the browser must preserve the denial explicitly instead of rendering guessed or cached protected content.

Admin configuration cannot rewrite historical workflow truth, lifecycle state, approval state, action execution state, reconciliation state, audit-export truth, release truth, gate truth, or closeout truth.

## 5. Negative Tests

Negative tests must reject support operator workflow authority, external collaborator workflow authority, UI role cache as authority, self-approval through role confusion, and admin configuration rewriting historical truth.

Negative tests must cite `docs/phase-51-6-authority-boundary-negative-test-policy.md` for UI cache, browser state, tickets, assistant output, downstream receipts, demo data, and other subordinate shortcut rejection when those surfaces are touched.

## 6. Scope Boundaries

This contract does not implement user or role administration, source administration, action policy administration, retention administration, audit export administration, AI enablement administration, tenant modeling, supportability breadth, reporting breadth, SOAR breadth, RC readiness, GA readiness, or commercial replacement claims.

Existing backend authority and reread-after-write posture remain unchanged.

## 7. Verification Commands

Run `npm test --workspace apps/operator-ui -- --run src/auth/roleMatrix.test.ts src/auth/session.test.ts`.

Run `bash scripts/verify-phase-57-1-rbac-role-matrix-contract.sh`.

Run `bash scripts/test-verify-phase-57-1-rbac-role-matrix-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1207 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1208 --config <supervisor-config-path>`.
