# Customer-Like Rehearsal Environment

## 1. Purpose and Boundary

This document defines the disposable customer-like rehearsal environment for the Phase 37 single-customer live rehearsal gate.

The rehearsal exists to replay the reviewed first-boot to single-customer operating path before AegisOps is treated as ready for a single-customer pilot.

It is anchored to `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, `docs/deployment/runtime-smoke-bundle.md`, `docs/deployment/operational-evidence-handoff-pack.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, and `control-plane/deployment/first-boot/`.

The rehearsal environment must be disposable, customer-like, and free of private customer context. It must not add HA, Kubernetes, multi-customer packaging, customer-private credentials, direct backend exposure, optional extension requirements, or vendor-specific automation.

## 2. Disposable Topology

The smallest approved rehearsal topology is:

- one disposable operator workstation or VM with repository access and Docker Compose;
- the repo-owned first-boot compose surface in `control-plane/deployment/first-boot/docker-compose.yml`;
- PostgreSQL as the authoritative AegisOps control-plane persistence dependency;
- the AegisOps control-plane service from `control-plane/`;
- the approved reverse proxy boundary as the only user-facing ingress path; and
- a reviewed Wazuh-facing intake path admitted through the reverse proxy and control-plane boundary.

The rehearsal uses one named rehearsal customer scope such as `<rehearsal-customer-id>`, but that value is a reviewed rehearsal binding only. Operators must not infer tenant, customer, source, account, repository, or environment linkage from names, comments, paths, hostnames, or nearby metadata.

The first-boot to single-customer delta is operational rather than architectural: the service boundary stays control plane, PostgreSQL, reverse proxy, and Wazuh-facing intake, while the operator evidence changes to customer-scoped ownership, daily queue and health review, backup custody, restore rehearsal, secret rotation, and break-glass custody.

## 3. Services and Ports

The required rehearsal services are limited to:

| Service | Required role | Exposure |
| --- | --- | --- |
| Reverse proxy | User-facing ingress for health, readiness, runtime inspection, protected read-only inspection, operator UI, and Wazuh-facing intake admission | Bind only the reviewed rehearsal proxy port such as `AEGISOPS_FIRST_BOOT_PROXY_PORT` |
| Control plane | Authoritative AegisOps record, readiness, runtime, inspection, approval, evidence, execution, and reconciliation surface | Internal only; do not publish the backend port as a front door |
| PostgreSQL | Authoritative AegisOps-owned state | Internal only; persistent data and backup targets stay separated |
| Wazuh-facing intake path | Reviewed analytic-signal intake into AegisOps-owned records | Through the reverse proxy and required intake secret boundary |

The default reviewed command remains:

```sh
docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml up -d
```

Health, readiness, runtime inspection, and smoke checks must use the reverse proxy:

```sh
curl -fsS http://127.0.0.1:<proxy-port>/healthz
curl -fsS http://127.0.0.1:<proxy-port>/readyz
curl -fsS <trusted-platform-admin-proxy-auth-headers> http://127.0.0.1:<proxy-port>/runtime
```

## 4. Required Runtime Inputs

Operators must prepare an untracked runtime env file from `control-plane/deployment/first-boot/bootstrap.env.sample`.

The required non-secret runtime values are:

- `AEGISOPS_CONTROL_PLANE_HOST`;
- `AEGISOPS_CONTROL_PLANE_PORT`;
- `AEGISOPS_CONTROL_PLANE_BOOT_MODE`;
- `AEGISOPS_CONTROL_PLANE_LOG_LEVEL`;
- `AEGISOPS_FIRST_BOOT_PROXY_PORT`;
- `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS`;
- `AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS`;
- `AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT`; and
- `AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER`.

The PostgreSQL DSN must resolve from either `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`, `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE`, or `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH`.

Each required secret must resolve from a reviewed file binding or OpenBao binding:

- Wazuh ingest shared secret from `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE` or `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH`;
- Wazuh ingest reverse-proxy secret from `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE` or `AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH`;
- protected-surface reverse-proxy secret from `AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE` or `AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH`;
- admin bootstrap token from `AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE` or `AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH`; and
- break-glass token from `AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE` or `AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH`.

If an OpenBao path is used for any required secret, the rehearsal env must also provide a reviewed OpenBao binding through `AEGISOPS_OPENBAO_ADDRESS` plus either `AEGISOPS_OPENBAO_TOKEN_FILE` or a runtime-injected `AEGISOPS_OPENBAO_TOKEN`, and `AEGISOPS_OPENBAO_KV_MOUNT`.

Missing, empty, placeholder, TODO, sample, fake, guessed, or unsigned values are not approved rehearsal inputs. The rehearsal must stop and remain failed closed until a trusted binding is available.

## 5. Approved Assumptions

Environment assumptions:

- the rehearsal env file is untracked and scoped to the disposable rehearsal;
- `AEGISOPS_CONTROL_PLANE_BOOT_MODE` remains `first-boot`; and
- optional extension URL variables may remain unset.

Secret assumptions:

- live DSNs, tokens, customer credentials, certificates, and break-glass material stay outside Git;
- file or OpenBao bindings may be checked for presence, but secret values must not be echoed into evidence; and
- placeholder credentials are refused even when they appear in sample files.

Reverse-proxy assumptions:

- the reverse proxy is the only reviewed user-facing ingress path;
- forwarded headers and identity fields are trusted only after the reviewed proxy and identity-provider boundary authenticates and normalizes them; and
- direct backend, PostgreSQL, or secret-backend publication is not part of the rehearsal.

Storage assumptions:

- PostgreSQL state uses a dedicated runtime mount;
- backup output is separated from primary runtime data; and
- VM snapshots may support infrastructure rollback but do not replace PostgreSQL-aware backup and restore validation.

Wazuh-facing intake assumptions:

- Wazuh remains an upstream detection substrate;
- intake admission requires the reviewed shared-secret and reverse-proxy secret boundary; and
- admitted signals become AegisOps-owned records only after the control-plane boundary validates and persists them.

## 6. Rehearsal Flow

The reviewed rehearsal sequence is:

1. Create a disposable rehearsal workspace or VM and select the reviewed repository revision.
2. Copy `control-plane/deployment/first-boot/bootstrap.env.sample` into an untracked `<runtime-env-file>`.
3. Replace placeholders with reviewed rehearsal values and trusted secret references without storing live values in Git.
4. Run `scripts/verify-customer-like-rehearsal-environment.sh --env-file <runtime-env-file>` before startup.
5. Start the stack through the repo-owned first-boot compose command.
6. Run the Phase 33 runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md` through the reverse proxy.
7. Capture the evidence required by `docs/deployment/operational-evidence-handoff-pack.md`.
8. Shut down the disposable stack through the runbook and confirm no rehearsal state is treated as customer production truth.

The rehearsal passes only when startup, readiness, runtime inspection, protected read-only inspection, backup custody, customer-scoped ownership, and clean-state evidence can be shown without widening the reviewed boundary.

## 7. Optional Extensions

Assistant, ML shadow, endpoint evidence, optional network evidence, OpenSearch, n8n, Shuffle, and isolated-executor paths remain disabled by default, unavailable, or explicitly non-blocking.

Optional extensions must not become startup prerequisites, readiness gates, smoke prerequisites, upgrade success gates, evidence handoff prerequisites, or reasons to widen the control-plane, PostgreSQL, reverse-proxy, or Wazuh-facing boundary.

If an optional extension is present in a rehearsal, it must be recorded as subordinate evidence only and must not redefine approval, evidence, execution, reconciliation, readiness, runtime scope, or intake authority.

## 8. Fail-Closed Validation

The focused rehearsal verifier is:

```sh
scripts/verify-customer-like-rehearsal-environment.sh --env-file <runtime-env-file>
```

The verifier must fail when the rehearsal document is missing, cross-links are missing, required runtime inputs are absent, secret bindings are absent, placeholder values are still present, `AEGISOPS_CONTROL_PLANE_BOOT_MODE` is not `first-boot`, optional extensions are described as prerequisites, or publishable guidance uses workstation-local absolute paths.

Rejected startup, intake, restore, upgrade, or smoke attempts must also prove that no orphan customer-scoped record, partial durable write, half-restored state, or misleading handoff evidence survived the failed path.

## 9. Out of Scope

HA, Kubernetes, multi-node operation, multi-customer operation, customer-private credentials, direct customer production access, optional-service auto-installation, endpoint or network evidence prerequisites, assistant or ML prerequisites, broad E2E validation, and vendor-specific deployment automation are out of scope.

This environment does not authorize external substrates as AegisOps authority. Wazuh, backup tooling, proxy logs, and runtime smoke output remain evidence around the AegisOps record chain, not substitutes for it.
