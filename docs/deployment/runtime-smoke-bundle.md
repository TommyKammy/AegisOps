# Phase 33 Runtime Smoke Bundle

## 1. Purpose and Scope

This document is the reviewed Phase 33 runtime smoke bundle for single-customer operator handoff after deployment or upgrade.

It is intentionally smaller than exhaustive E2E validation and proves only the post-deployment confidence path needed before normal business-hours operation resumes.

The bundle is anchored to `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, and `control-plane/deployment/first-boot/`.

The reviewed smoke path covers startup status, readiness, protected-surface reachability, operator-console read-only sanity, queue/read-only surface sanity, and first low-risk action preconditions.

It does not require optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, or isolated-executor extensions to be enabled.

Operators must run the smoke bundle through the approved reverse proxy boundary, not by publishing the control-plane backend port directly.

## 2. Preconditions

Run this smoke bundle after the repo-owned first-boot startup path has completed during a single-customer deployment, reviewed upgrade, rollback, or operator handoff window.

The operator has a prepared untracked runtime env file copied from `control-plane/deployment/first-boot/bootstrap.env.sample`.

The operator has a named repository revision or release identifier for the handoff record.

The operator has the reviewed proxy authentication headers or equivalent trusted proxy session needed for protected read-only inspection without writing those secret values into the evidence record.

The approved reverse proxy is the user-facing ingress path for the smoke window, and the backend control-plane port remains internal.

Optional extension URLs, tokens, sidecars, or packages may remain unset.

Stop the smoke and keep the handoff blocked if required runtime config, trusted proxy authentication, readiness, or record-scope signals are missing, malformed, or contradictory.

## 3. Smoke Commands

Capture startup status from the repo-owned compose surface:

```sh
docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml ps
```

Capture a bounded startup or upgrade-window log sample:

```sh
docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml logs --tail=200
```

Confirm liveness through the reviewed reverse proxy:

```sh
curl -fsS http://127.0.0.1:<proxy-port>/healthz
```

Confirm readiness through the reviewed reverse proxy:

```sh
curl -fsS http://127.0.0.1:<proxy-port>/readyz
```

For protected surfaces, substitute `<trusted-platform-admin-proxy-auth-headers>` or `<trusted-operator-read-only-proxy-auth-headers>` with the reviewed proxy session header arguments. Those arguments must come from the trusted proxy or equivalent reviewed operator session, not from sample, fake, or operator-invented values.

The protected header set is:

- `X-Forwarded-Proto: https`
- `X-AegisOps-Proxy-Secret: <reviewed-proxy-secret>`
- `X-AegisOps-Proxy-Service-Account: <reviewed-proxy-service-account>`
- `X-AegisOps-Authenticated-IdP: <reviewed-identity-provider>`
- `X-AegisOps-Authenticated-Subject: <reviewed-operator-subject>`
- `X-AegisOps-Authenticated-Identity: <reviewed-operator-identity>`
- `X-AegisOps-Authenticated-Role: <reviewed-operator-role>`

Use a reviewed `platform_admin` role for `<trusted-platform-admin-proxy-auth-headers>` because `/runtime` is platform-admin protected. Use a reviewed `analyst`, `approver`, or `platform_admin` role for `<trusted-operator-read-only-proxy-auth-headers>` because the read-only inspection routes accept those operator roles.

Confirm protected runtime inspection through the reviewed proxy and trusted operator boundary:

```sh
curl -fsS <trusted-platform-admin-proxy-auth-headers> http://127.0.0.1:<proxy-port>/runtime
```

Confirm read-only alert visibility through the reviewed proxy:

```sh
curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=alerts"
```

Confirm read-only case visibility through the reviewed proxy:

```sh
curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=cases"
```

Confirm action-review records are inspectable without creating a new request:

```sh
curl -fsS <trusted-operator-read-only-proxy-auth-headers> "http://127.0.0.1:<proxy-port>/inspect-records?family=action_requests"
```

Confirm reconciliation status remains readable from the protected mainline surface:

```sh
curl -fsS <trusted-operator-read-only-proxy-auth-headers> http://127.0.0.1:<proxy-port>/inspect-reconciliation-status
```

If a command returns an authentication refusal, readiness refusal, route refusal, or contradictory runtime scope, preserve that exact result in the handoff record and stop instead of retrying through an unreviewed path.

## 4. Handoff Checklist

- Startup status: the repo-owned compose stack shows the expected first-boot services and the bounded logs do not contain unresolved runtime-config, PostgreSQL reachability, migration, or reverse-proxy admission failures.
- Readiness: `/healthz` and `/readyz` succeed through the approved reverse proxy, and readiness is not inferred from container existence alone.
- Protected surface: `/runtime` succeeds only through the reviewed trusted-proxy or equivalent operator boundary, and missing or fake authentication remains blocked.
- Runtime scope: `/runtime` still describes the reviewed first-boot and single-customer surface rather than optional-extension, HA, multi-customer, or direct-backend expansion.
- Queue/read-only sanity: alert, case, action-request, and reconciliation inspection commands return bounded read-only data or an explicit empty state from the protected mainline surface.
- Operator-console sanity: Confirm the operator console can render `/operator/queue` or the configured operator-console base path with the same reviewed backend session, then keep the check read-only.
- First low-risk action preconditions: Confirm the first candidate low-risk action remains in precondition review only: a reviewed alert or case is selected, an allowed low-risk action type is identified, approver ownership is known, and no action request, approval decision, delegation, executor dispatch, or reconciliation write is performed by this smoke bundle.
- Evidence: command output is attached to the deployment, upgrade, rollback, or handoff record without secret values.

## 5. Evidence and Health-Review Fit

The smoke result must be attached to the deployment, upgrade, or handoff record and referenced by the next daily queue and health review.

For daily business-day health review, the smoke result is a recent handoff checkpoint only. Operators still review readiness, runtime scope, the queue and alert surfaces, degraded-state markers, and escalation conditions under `docs/runbook.md`.

The weekly platform hygiene review still owns certificate expiry, storage growth, backup drift, and restore-readiness evidence.

For post-upgrade checks, compare the post-change smoke result with the pre-change readiness, runtime, compose status, queue, and bounded-log evidence before closing the maintenance window.

For rollback checks, run this bundle after the documented restore or rollback path and keep normal operation blocked if the restored state cannot prove the same first-boot scope, protected ingress, and read-only record-chain visibility.

## 6. Out of Scope

Full workflow regression, optional-extension full-path validation, broad source coverage, destructive action validation, and exhaustive E2E validation are out of scope.

This smoke bundle does not validate optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, isolated-executor, HA, multi-customer, or vendor-specific deployment automation paths.

This smoke bundle does not approve direct backend exposure, placeholder credentials, unsigned identity hints, inferred customer binding, or action execution without the reviewed approval, delegation, and reconciliation boundaries.
