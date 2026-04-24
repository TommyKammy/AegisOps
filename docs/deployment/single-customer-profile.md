# Single-Customer Deployment Profile

## 1. Package Status

This document is the repo-owned single-customer deployment profile package for the reviewed Phase 33 deployment boundary.

It packages the current first-boot runtime surface into the default reviewed deployment shape for one customer environment without adding multi-customer, HA, or optional-service prerequisites.

The package is anchored to `docs/runbook.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, and `control-plane/deployment/first-boot/`.

This package is operational guidance for the reviewed single-customer profile. It does not store customer-specific values, live secrets, DSNs, certificates, tokens, or vendor automation settings.

The customer-like rehearsal environment in `docs/deployment/customer-like-rehearsal-environment.md` defines the disposable topology and preflight validation used to rehearse this profile without private customer context.

Package inventory:

| Artifact | Role in this package |
| --- | --- |
| `docs/deployment/single-customer-profile.md` | Reviewed operator-facing package boundary for one customer environment |
| `docs/deployment/customer-like-rehearsal-environment.md` | Disposable customer-like rehearsal topology and fail-closed preflight validation |
| `control-plane/deployment/first-boot/docker-compose.yml` | Repo-owned startup surface for the current control-plane, PostgreSQL, and proxy stack |
| `control-plane/deployment/first-boot/bootstrap.env.sample` | Approved runtime input template to copy into an untracked customer-specific env file |
| `docs/runbook.md` | Startup, shutdown, upgrade, restore, rollback, secret-rotation, and evidence procedure |
| `docs/smb-footprint-and-deployment-profile-baseline.md` | Reviewed single-customer cadence, backup, restore, upgrade, and ownership expectations |
| `docs/network-exposure-and-access-path-policy.md` | Reverse-proxy and internal-service exposure policy |
| `docs/storage-layout-and-mount-policy.md` | PostgreSQL storage and backup separation policy |

## 2. Deployable Shape

The required services for this profile are limited to:

- AegisOps control-plane service from `control-plane/`;
- PostgreSQL for authoritative AegisOps-owned state;
- the approved reverse proxy boundary as the only reviewed user-facing ingress path; and
- the Wazuh-facing analytic-signal intake path admitted through the reviewed proxy and control-plane boundary.

The approved repo-owned startup surface remains `control-plane/deployment/first-boot/docker-compose.yml` with `control-plane/deployment/first-boot/bootstrap.env.sample` copied into an untracked runtime env file.

The service order remains PostgreSQL dependency first, then control-plane runtime-config validation, PostgreSQL reachability proof, and migration bootstrap, then reverse-proxy admission. Partial container creation is not readiness.

The reviewed profile assumes one named customer environment, one reviewed control-plane state boundary, and one operator-owned evidence trail for startup, shutdown, upgrade, restore, and rollback windows.

## 3. Approved Inputs

The approved required runtime inputs are:

- `AEGISOPS_CONTROL_PLANE_HOST`;
- `AEGISOPS_CONTROL_PLANE_PORT`;
- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`;
- `AEGISOPS_CONTROL_PLANE_BOOT_MODE`; and
- `AEGISOPS_CONTROL_PLANE_LOG_LEVEL`.

The approved secret and boundary inputs are the PostgreSQL credential source, the Wazuh ingest shared secret source, the Wazuh ingest reverse-proxy secret source, the protected-surface reverse-proxy secret source, the protected-surface trusted proxy CIDRs, the protected-surface proxy service account, the reviewed identity-provider binding, the admin bootstrap token source, the break-glass token source, and any reviewed OpenBao address, token, token-file, and mount bindings used to resolve those secrets.

Live secret values, customer credentials, DSNs, bootstrap tokens, break-glass tokens, and environment-specific certificates must stay outside Git.

Configuration values must be explicit, reviewed, and bound to the named customer environment. Operators must not infer customer, tenant, repository, account, source, or environment linkage from naming conventions, path shape, comments, or nearby metadata alone.

Placeholder credentials, sample tokens, empty secret paths, unsigned identity hints, and TODO values are not approved runtime inputs. Startup, rotation, restore, or upgrade work must stop until a trusted credential source and reviewed binding are available.

## 4. Service and Path Boundary

The reverse proxy is the only reviewed user-facing ingress path for health, readiness, runtime inspection, operator UI, and Wazuh-facing intake admission.

The control-plane backend port, PostgreSQL port, and secret backend are internal service surfaces and must not become independently published front doors.

The Wazuh-facing path is a substrate-detection intake path into AegisOps-owned records, not a direct Wazuh-to-automation or Wazuh-owned case-authority shortcut.

Forwarded headers, host hints, tenant hints, source labels, and client-supplied user identity fields are not trusted unless the reviewed proxy and identity-provider boundary has authenticated, normalized, and bound them to the request.

The control plane remains the authority for approval, evidence, action-execution, and reconciliation records. PostgreSQL stores that AegisOps-owned record chain; Wazuh remains an upstream detection substrate.

## 5. First-Boot to Single-Customer Delta

The single-customer profile keeps the same first-boot service boundary but changes the operator-visible operating contract from a lab rehearsal to one named customer environment.

The single-customer delta is daily business-day queue and health review, weekly platform hygiene review, daily PostgreSQL-aware backup, weekly backup review, pre-change configuration backup, monthly restore rehearsal, one planned maintenance window per month, named customer-scoped approver ownership, reviewed secret rotation, and explicit break-glass custody for customer credentials.

The delta does not add direct backend exposure, browser authority, substrate authority, direct automation shortcuts, HA topology, multi-customer coordination, or optional-service installation.

Readiness and runtime inspection still prove the reviewed first-boot contract: valid required runtime inputs, PostgreSQL reachability, migration bootstrap success, reverse-proxy admission, and no hidden dependency on optional services.

Customer-visible operation begins only after the operator can show the startup evidence, reverse-proxy health and readiness checks, runtime inspection, backup custody, and customer-scoped approval and secret ownership expected by the runbook.

## 6. Optional Extensions

Optional OpenSearch, n8n, Shuffle, endpoint evidence, optional network evidence, assistant, ML shadow, and isolated-executor paths are disabled by default, unavailable, or explicitly non-blocking unless a later reviewed package enables one for a bounded purpose.

Optional extensions must not become startup prerequisites, readiness gates, upgrade success gates, or reasons to widen the control-plane, PostgreSQL, reverse-proxy, or Wazuh-facing boundary.

If an optional surface is displayed, it must remain subordinate to the authoritative control-plane record chain and must report `disabled_by_default`, `unavailable`, `degraded`, or `enabled` only from reviewed backend-owned state.

Operators must not repair optional-extension absence by adding endpoint, network, assistant, ML, or automation prerequisites to this deployment package.

## 7. Upgrade and Same-Day Rollback Rehearsal Contract

The Phase 33 upgrade rehearsal is the single-customer maintenance-window exercise that proves a reviewed repository revision can be introduced and, if needed, returned to the prior known-good state the same day.

Before the rehearsal begins, operators must confirm the daily PostgreSQL-aware backup is current, the pre-change configuration backup has been captured, the restore point for rollback is named, and the backup custody record identifies the operator or break-glass owner for the window.

The rehearsal assumes one planned business-hours maintenance window for the named customer environment, not zero-downtime rollout, HA failover, multi-region recovery, or infrastructure-vendor-specific upgrade tooling.

Rollback decision review happens before the maintenance window closes and must choose one of two recorded outcomes: keep the upgraded revision only if post-upgrade checks pass, or start same-day rollback to the selected restore point if readiness, runtime inspection, reverse-proxy boundary, or record-chain trust cannot be proven.

Post-upgrade smoke checks are the reviewed runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md`: reverse-proxy `/readyz`, reverse-proxy `/runtime`, repo-owned compose status, bounded upgrade-window logs, and operator-visible queue or alert review from the mainline surface.

Restore compatibility for the rehearsal is inherited from the Phase 32 runbook baseline: approval, evidence, execution, and reconciliation records must return cleanly from the selected PostgreSQL-aware restore point before normal operation resumes.

The rehearsal evidence must retain the maintenance-window approval, named operator, pre-change backup custody confirmation, selected restore point, before-and-after repository revisions, pre-change and post-change smoke results, rollback decision, and any post-rollback restore validation.

The Phase 33 operational evidence handoff pack in `docs/deployment/operational-evidence-handoff-pack.md` defines the minimal retained audit package for upgrade, restore, approval, execution, and reconciliation events.

## 8. Day-2 Operating Shape

Day-2 operation follows the cadence in `docs/runbook.md` and `docs/smb-footprint-and-deployment-profile-baseline.md` for the reviewed single-customer profile.

Operators must preserve PostgreSQL-aware backup custody, restore validation for approval, evidence, execution, and reconciliation records, same-day rollback readiness, certificate and storage-growth hygiene review, and reviewed secret rotation evidence.

Backup, restore, export, readiness, and detail rollup evidence must represent one committed runtime state. If an operator detects mixed-snapshot results, partial restore state, orphan records, or half-restored records, normal operation must stay blocked until the durable state is clean.

Rejected startup, rotation, restore, upgrade, or intake attempts must leave no new authoritative customer-scoped record, partial durable write, orphan evidence item, or half-restored state that later operators could mistake for truth.

## 9. Out of Scope

HA topology, multi-customer packaging, optional-service auto-installation, vendor-specific deployment automation, direct browser authority, direct substrate authority, and endpoint, network, assistant, or ML shadow paths as deployment prerequisites are out of scope.

This package also does not approve broad source coverage, enterprise-cluster sizing, dedicated database-team operation, continuous overnight staffing, or fleet-wide MSSP coordination.
