# AegisOps Phase 17 Runtime Config Contract and Boot Command Expectations

## 1. Purpose

This document defines the concrete runtime config contract and boot command expectations for the Phase 17 first-boot bring-up path.

It supplements `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/control-plane-runtime-service-boundary.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, and `control-plane/deployment/first-boot/`.

This document turns the approved Phase 16 floor into a concrete implementation contract for image, Compose, and entrypoint work without broadening first-boot scope.

It does not approve live Wazuh integration wiring, a thin operator UI, optional OpenSearch extension wiring, or the high-risk executor path.

## 2. Phase 17 Contract Goal

Phase 17 exists to make the approved first-boot target bootable as a real control-plane runtime service.

That means the repository must now be explicit about:

- which runtime environment keys are required to start the control-plane service process;
- which keys may use reviewed defaults;
- which optional keys remain non-blocking and deferred;
- which boot command shape is approved for the control-plane service process;
- how migration bootstrap is sequenced before normal service readiness; and
- how the reverse proxy remains the only approved user-facing exposure path.

Phase 17 therefore defines implementation expectations for the approved first-boot runtime.

It does not reopen which components count as the runtime floor.

## 3. Runtime Config Contract

### 3.1 Approved Required Runtime Environment Keys

The approved required runtime environment keys for Phase 17 first boot are:

- `AEGISOPS_CONTROL_PLANE_HOST`
- `AEGISOPS_CONTROL_PLANE_PORT`
- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`
- `AEGISOPS_CONTROL_PLANE_BOOT_MODE`
- `AEGISOPS_CONTROL_PLANE_LOG_LEVEL`

`AEGISOPS_CONTROL_PLANE_HOST` is required runtime input because the service must bind intentionally to the approved internal interface rather than to an inferred convenience default.

`AEGISOPS_CONTROL_PLANE_PORT` is required runtime input for the reviewed listen port, even when repository-local boot surfaces provide a reviewed default.

`AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` is required authoritative persistence configuration and must identify the reviewed PostgreSQL control-plane datastore.

`AEGISOPS_CONTROL_PLANE_BOOT_MODE` is required so the boot command can distinguish first-boot migration-and-serve behavior from unsupported ad hoc startup modes.

`AEGISOPS_CONTROL_PLANE_LOG_LEVEL` is required so runtime observability is explicit and reviewable instead of being hidden inside framework defaults.

If any required key is absent, empty, malformed, contradictory, or would violate the approved reverse-proxy-first exposure model, startup must fail closed.

### 3.2 Approved Defaults and Fail-Closed Rules

The following reviewed local defaults are allowed only where they preserve the approved first-boot boundary:

- `AEGISOPS_CONTROL_PLANE_HOST=0.0.0.0` for Compose-backed first boot where the backend port remains unpublished and reachable only through the internal network path behind the approved reverse proxy
- `AEGISOPS_CONTROL_PLANE_HOST=127.0.0.1`
- `AEGISOPS_CONTROL_PLANE_PORT=8080`
- `AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot`
- `AEGISOPS_CONTROL_PLANE_LOG_LEVEL=INFO`

`AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` has no approved repository default and must come from an untracked runtime secret source or operator-provided runtime env file.

`AEGISOPS_CONTROL_PLANE_HOST` must fail closed if set to an ambiguous or exposure-bypassing wildcard that cannot preserve the approved reverse-proxy-first boundary, including `::` or `*`.

`AEGISOPS_CONTROL_PLANE_HOST=0.0.0.0` is approved only for internal repository-local boot surfaces where the control-plane backend port remains unpublished and the approved reverse proxy remains the sole user-facing ingress path.

`AEGISOPS_CONTROL_PLANE_PORT` must fail closed if it is non-numeric, empty, or outside the reviewed application listen-port expectation.

`AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` must fail closed unless it is a PostgreSQL DSN for the AegisOps-owned control-plane datastore boundary.

`AEGISOPS_CONTROL_PLANE_BOOT_MODE` must fail closed unless it is the reviewed first-boot mode expected by the repository-local entrypoint and service command path.

`AEGISOPS_CONTROL_PLANE_LOG_LEVEL` must fail closed unless it is one of the reviewed service levels `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

### 3.3 Approved Optional and Deferred Environment Keys

The approved optional and deferred environment keys remain:

- `AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL`
- `AEGISOPS_CONTROL_PLANE_N8N_BASE_URL`
- `AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL`
- `AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL`

These keys may be present in runtime env files or Compose wiring for future compatibility, but they must not become first-boot prerequisites.

Their absence must not block control-plane startup, migration bootstrap, liveness, or readiness for the reviewed Phase 17 first-boot path.

## 4. Boot Command Expectations

### 4.1 Control-Plane Service Process

The approved control-plane boot path is a reviewed entrypoint that validates runtime config, runs migration bootstrap, proves readiness prerequisites, and then starts the control-plane service process.

The control-plane service process must be started as the final foreground process for the container or runtime unit.

The reviewed boot command shape is:

1. validate required runtime config
2. validate the reviewed migration asset set
3. prove PostgreSQL reachability
4. apply the required forward migration bootstrap set
5. verify the expected first-boot schema state
6. exec the control-plane service process

The boot command must not background the control-plane service process, split migration bootstrap into an undocumented sidecar, or report readiness before migration bootstrap succeeds.

### 4.2 Migration Bootstrap Expectations

Migration bootstrap remains part of the approved normal boot sequence for `AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot`.

The reviewed migration asset home remains `postgres/control-plane/migrations/`.

Migration bootstrap must execute before the control-plane service process is treated as ready for authoritative writes.

Migration bootstrap failure includes:

- missing reviewed migration assets;
- PostgreSQL connection failure;
- a failed forward migration;
- partially applied required migrations; or
- inability to prove the expected reviewed schema state after migration execution.

Any such failure must fail closed and stop the boot command before normal service admission.

### 4.3 Reverse-Proxy Exposure Model

Phase 17 keeps the approved reverse proxy as the only reviewed user-facing ingress path.

The control-plane backend port must remain an internal service port.

Repository-local boot surfaces must not publish the control-plane backend port directly to user networks or the public internet.

The contract therefore must not publish the control-plane backend port directly as a substitute for approved reverse-proxy routing.

Compose, container, or service-unit examples may expose the reverse proxy front door, but they must keep the control-plane service on an internal network path behind that proxy.

## 5. Phase 16 Placeholders That Become Concrete Runtime Expectations

Phase 16 placeholders become concrete runtime expectations in Phase 17 as follows:

- the reviewed first-boot skeleton environment keys now become the approved runtime environment contract for first boot;
- the reviewed first-boot entrypoint pattern now becomes the approved boot sequencing contract for real bring-up work;
- the reviewed migration asset location now becomes the required runtime migration-bootstrap input;
- the reviewed distinction between liveness and readiness now becomes a concrete startup gate for implementation; and
- the reviewed reverse-proxy-first access model now becomes a concrete exposure rule for image and Compose work.

The following items remain deferred and must stay visibly out of the initial bring-up contract:

- live Wazuh integration wiring;
- optional OpenSearch extension wiring or OpenSearch-dependent readiness;
- n8n, Shuffle, or executor connectivity as startup blockers;
- the thin operator UI or analyst-assistant surface; and
- destructive schema repair, downgrade logic, or ad hoc bootstrap shortcuts.

## 6. Alignment and Non-Expansion Rules

This Phase 17 contract is aligned to the Phase 16 first-boot scope and must be read as a concrete implementation contract for that already-approved floor.

If an image, Compose definition, runtime env file, or service unit conflicts with this document by adding new required dependencies, direct backend publication, or broader first-boot success criteria, that implementation is out of contract and must fail review.

`docs/phase-16-release-state-and-first-boot-scope.md` remains the normative source for the approved runtime floor.

`docs/network-exposure-and-access-path-policy.md` remains the normative source for the reverse proxy and internal exposure rules.

`docs/control-plane-runtime-service-boundary.md` remains the normative source for the ownership split and the `control-plane/` runtime home.
