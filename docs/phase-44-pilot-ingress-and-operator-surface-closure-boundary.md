# AegisOps Phase 44 Pilot Ingress and Operator Surface Closure Boundary

## 1. Purpose

This document defines the reviewed Phase 44 pilot ingress and operator surface closure boundary.

It retroactively closes the Phase 44 contract around the first-boot proxy operator surface, protected identity header normalization, backend and operator-ui role canonicalization, runtime smoke ingress evidence, and the operator-ui CI gate.

It supplements `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/phase-31-product-grade-hardening-boundary.md`, `docs/deployment/runtime-smoke-bundle.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/runbook.md`, and `docs/architecture.md`.

This document describes the closed Phase 44 ingress and operator surface contract only. It does not change runtime behavior, operator UI behavior, route exposure, identity posture, role posture, or workflow authority.

## 2. In Scope

Phase 44 closes one narrow pilot ingress and operator surface contract:

- the repo-owned first-boot proxy remains the reviewed operator ingress surface for health, readiness, runtime inspection, read-only operator inspection, and the bounded operator queue path;
- protected identity headers are stripped or normalized at the reviewed proxy boundary before backend authorization evaluates them;
- backend protected-surface authentication remains the enforcement boundary for reviewed identity provider, subject, identity, role, proxy secret, proxy service account, HTTPS, and trusted peer signals;
- backend and operator-ui role canonicalization stay aligned around reviewed roles such as `analyst`, `approver`, and `platform_admin`;
- runtime smoke ingress evidence remains a bounded proof that the reviewed proxy path can reach protected runtime and operator inspection routes without performing write-capable workflow actions; and
- the operator-ui CI gate remains the reviewed frontend quality gate for typecheck, tests, and build before the operator surface is treated as pilot-ready.

The Phase 44 boundary is an ingress and validation closure. It records that the pilot path is understandable from repo-owned artifacts without promoting browser state, proxy logs, smoke output, assistant output, tickets, or downstream receipts into workflow truth.

## 3. Out of Scope

Phase 44 does not authorize:

- new proxy routes or runtime endpoints;
- new operator UI features;
- a new role model or production RBAC design;
- direct backend exposure;
- production identity-provider rollout beyond the reviewed protected-surface contract;
- browser-owned authorization, lifecycle, approval, execution, reconciliation, or audit truth;
- write-capable operator workflow expansion;
- optional extension promotion into the mainline pilot ingress path; or
- treating Browser state, operator UI state, external tickets, assistant output, and downstream receipts as workflow truth.

Direct backend exposure remains outside the reviewed pilot path. Operators and verifiers must use the reviewed proxy boundary and repo-owned commands rather than bypassing the proxy to make a failing ingress path appear healthy.

## 4. First-Boot Proxy Operator Surface

The reviewed first-boot proxy operator surface is anchored in `control-plane/deployment/first-boot/docker-compose.yml` and `proxy/nginx/conf.d-first-boot/control-plane.conf`.

The proxy surface may expose only the reviewed first-boot and operator-inspection route families needed for the pilot closure:

- `/healthz`;
- `/readyz`;
- `/runtime`;
- `/inspect-records`;
- `/inspect-reconciliation-status`;
- `/inspect-analyst-queue`;
- `/inspect-alert-detail`;
- `/inspect-case-detail`;
- `/inspect-action-review`;
- `/inspect-advisory-output`; and
- `/operator/queue`.

The read-only inspection routes and queue alias must keep their read-only method posture. The proxy must not expose operator write routes, administrative bootstrap routes, or direct backend internals as part of Phase 44.

## 5. Protected Identity Header Normalization

Protected identity header normalization happens at the reviewed proxy boundary before the backend evaluates protected-surface authorization.

The reviewed protected header family is:

- `X-AegisOps-Proxy-Secret`;
- `X-AegisOps-Proxy-Service-Account`;
- `X-AegisOps-Authenticated-IdP`;
- `X-AegisOps-Authenticated-Subject`;
- `X-AegisOps-Authenticated-Identity`; and
- `X-AegisOps-Authenticated-Role`.

The first-boot proxy must strip caller-supplied values for this header family until a reviewed authenticated identity source is wired into the boundary. The backend must then fail closed when required proxy, provider, subject, identity, role, peer, HTTPS, or credential signals are absent, malformed, placeholder-like, or inconsistent with the reviewed runtime config.

Raw `X-Forwarded-*`, `Forwarded`, host, proto, tenant, user-id, role, and identity hints are not trusted unless the reviewed proxy and identity-provider boundary has authenticated, normalized, and bound them to the request.

## 6. Role Canonicalization

Backend and operator-ui role canonicalization must remain explicit and aligned.

The backend receives canonical protected-surface roles and checks them against endpoint-specific allowed roles. The operator UI normalizes reviewed session role claims into lower-case canonical role names and filters them against the configured reviewed role set.

The reviewed pilot role family remains:

- `analyst`;
- `approver`; and
- `platform_admin`.

Missing roles, malformed role arrays, unreviewed role names, placeholder values, or role claims that are present only in client-controlled state must fail closed as unauthenticated, forbidden, or invalid-session behavior according to the applicable boundary.

The operator UI may render role-aware navigation and page posture as convenience behavior, but backend authorization remains authoritative for protected reads and any later write-capable workflow action.

## 7. Runtime Smoke Ingress Evidence

Runtime smoke ingress evidence is bounded evidence around the reviewed proxy path.

The reviewed evidence path is `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`.

That gate captures startup status, bounded logs, health, readiness, protected runtime inspection, read-only operator queue ingress, read-only detail ingress, and first low-risk action preconditions. It intentionally does not create reviewed action requests, approval decisions, delegation dispatches, executor writes, or reconciliation writes.

Runtime smoke output is evidence that the reviewed ingress path is reachable and retains the expected read-only posture. It is not workflow truth and must not override AegisOps backend records.

## 8. Operator-UI CI Gate

The operator-ui CI gate is the reviewed frontend gate for the pilot operator surface.

The CI workflow and verifier references are:

- `.github/workflows/ci.yml`;
- `scripts/test-verify-ci-operator-ui-workflow-coverage.sh`;
- `apps/operator-ui/src/auth/session.test.ts`;
- `apps/operator-ui/src/app/OperatorRoutes.test.tsx`;
- `apps/operator-ui/e2e/operator-workflows.spec.ts`; and
- `apps/operator-ui/playwright.config.ts`.

The gate proves the operator UI can typecheck, run its focused tests, and build against the reviewed session and route contract. It does not make the browser the authority for identity, role, record lifecycle, approval, execution, reconciliation, or audit truth.

## 9. Fail-Closed Conditions

Phase 44 must fail closed when any prerequisite boundary signal is missing, malformed, placeholder-like, or only partially trusted.

Blocking conditions include:

- the first-boot proxy route set is missing required reviewed routes or exposes write-capable or administrative routes outside the reviewed boundary;
- caller-supplied protected identity headers can pass through the first-boot proxy as trusted values;
- the protected-surface runtime lacks reviewed proxy CIDRs, proxy secret, proxy service account, or reviewed identity-provider binding when non-loopback protected-surface access is configured;
- protected-surface requests bypass the reviewed proxy peer boundary, omit HTTPS, use the wrong proxy credential, use the wrong proxy service account, omit reviewed identity provider, subject, identity, or role attribution, or present an unauthorized role;
- placeholder credentials such as `<set-me>` are accepted as runtime credentials;
- operator-ui session parsing treats malformed claims, empty roles, or unreviewed roles as valid access;
- runtime smoke evidence is captured through direct backend exposure rather than the reviewed proxy path; or
- operator UI, browser state, proxy evidence, tickets, assistant output, or downstream receipts are used as workflow truth instead of subordinate context.

When one of these conditions appears, the correct outcome is rejection, blocked readiness, forbidden access, invalid-session behavior, or an explicit follow-up. The system must not infer success from naming conventions, path shape, cached browser state, proxy reachability alone, or nearby metadata.

## 10. Authority Boundary Notes

AegisOps backend records remain authoritative for alert, case, evidence, recommendation, approval, action intent, execution receipt, reconciliation, lifecycle, readiness, and audit truth.

The first-boot proxy is an ingress and normalization boundary, not a workflow authority.

The operator UI is a thin client and subordinate surface, not a system of record.

Runtime smoke evidence proves bounded route reachability and expected read-only posture, not the truth of operational casework or workflow completion.

operator UI and proxy evidence do not become workflow truth.

Browser state, operator UI state, external tickets, assistant output, and downstream receipts remain subordinate context unless a reviewed AegisOps backend record explicitly binds them into the authoritative record chain.

Proxy logs, runtime smoke output, and optional substrate state remain subordinate context under the same rule.

## 11. Validation Expectations

Validation must remain documentation and boundary focused.

At minimum, validation should prove:

- the Phase 44 boundary and validation docs exist;
- the docs name in-scope, out-of-scope, fail-closed conditions, verifier references, and authority boundary notes;
- the first-boot proxy route and protected identity header normalization tests remain the evidence anchor for ingress closure;
- backend protected-surface auth tests remain the enforcement anchor for identity, role, proxy, and placeholder fail-closed behavior;
- operator-ui session tests remain the role canonicalization anchor;
- runtime smoke gate references remain repo-relative and use `<runtime-env-file>` and `<evidence-dir>` placeholders; and
- no runtime or UI behavior change is included.
