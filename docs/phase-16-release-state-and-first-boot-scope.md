# AegisOps Phase 16 Release-State and First-Boot Scope

## 1. Purpose

This document defines the approved Phase 16 release-state and first-boot scope for bootable AegisOps.

It supplements `docs/control-plane-runtime-service-boundary.md`, `docs/architecture.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, and `README.md` by narrowing Phase 16 to the minimum runtime shape that is allowed to count as the first bootable AegisOps release-state before Phase 17 runtime bring-up expands implementation detail.

This document defines release-state and review scope only. It does not approve concrete containerization, live Wazuh integration wiring, analyst UI implementation, or broad runtime expansion beyond the first-boot boundary described here.

## 2. Approved Phase 16 Release-State

The approved Phase 16 release-state is a repository baseline that is ready to enter Phase 17 runtime bring-up with one narrow bootability target.

That target is a bootable first-boot runtime composed of:

- the AegisOps control-plane service as the authoritative runtime boundary;
- PostgreSQL as the AegisOps-owned persistence dependency for control-plane state;
- the approved reverse proxy access boundary for controlled ingress; and
- reviewed Wazuh-facing runtime expectations for upstream analytic-signal intake.

Phase 16 release-state means those components are the required bootability floor.

It does not mean every adjacent substrate tracked in the repository must boot on day one, and it does not redefine optional repository assets as mandatory first-boot dependencies.

## 3. First-Boot In-Scope Runtime Components

The first bootable AegisOps runtime includes the following in-scope components:

- a live AegisOps control-plane service rooted under `control-plane/`;
- the reviewed PostgreSQL boundary for AegisOps-owned control-plane records;
- the approved reverse proxy path for controlled user-facing ingress and administrative exposure control; and
- reviewed runtime expectations that the control-plane service can accept Wazuh-originated analytic-signal inputs without requiring Wazuh to become the authority for downstream alert, case, approval, or reconciliation truth.

The first-boot scope is intentionally narrow.

It is limited to the minimum runtime needed to prove that AegisOps can boot around its own control-plane authority boundary instead of around optional analytics, optional orchestration, or future user-interface surfaces.

## 4. First-Boot Explicitly Out of Scope

The following items are explicitly out of scope for the Phase 16 first-boot release-state:

- optional OpenSearch extension runtime or OpenSearch-dependent first-boot success criteria;
- n8n as a required first-boot dependency or orchestration prerequisite;
- the full interactive analyst-assistant surface;
- the high-risk executor path or write-capable response execution; and
- broad source coverage beyond the narrow Wazuh-facing runtime expectation required for first boot.

These areas may remain repository-tracked, designed, or deferred, but they must not silently become blockers for the first bootable runtime target.

## 5. Phase 16 Definition of Done

Phase 16 is done when the repository baseline unambiguously states that:

- first boot requires the AegisOps control-plane service, PostgreSQL, and the approved reverse proxy boundary;
- Wazuh-facing runtime expectations are limited to reviewed upstream analytic-signal intake expectations rather than live end-to-end substrate wiring;
- OpenSearch, n8n, the full analyst-assistant surface, the high-risk executor, and broad source expansion remain optional, deferred, or non-blocking for first boot; and
- later phases can use this document as the bootability target for Phase 17 runtime bring-up without reopening what counts as the minimum first-boot runtime.

Phase 16 therefore ends with an approved bootability target, not with a claim that the full platform is feature-complete.

## 6. Bootstrap Environment Contract

The first-boot bootstrap environment contract exists to keep Phase 17 runtime bring-up narrow, reviewable, and fail-closed.

The required first-boot environment variables are:

- `AEGISOPS_CONTROL_PLANE_HOST` for the control-plane bind host;
- `AEGISOPS_CONTROL_PLANE_PORT` for the control-plane listen port;
- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` for the authoritative PostgreSQL connection string used by the control-plane runtime; and
- repository-local runtime wiring needed to keep the reverse proxy on the approved ingress path instead of exposing backend services directly.

`AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` is required bootstrap state for first boot.

`AEGISOPS_CONTROL_PLANE_HOST` and `AEGISOPS_CONTROL_PLANE_PORT` may use reviewed local defaults only when those defaults preserve the approved reverse-proxy-first access model.

Optional environment variables such as `AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL`, `AEGISOPS_CONTROL_PLANE_N8N_BASE_URL`, `AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL`, and `AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL` must not become first-boot prerequisites.

If required bootstrap state is absent, malformed, contradictory, or would bypass the approved reverse proxy boundary, the runtime must fail closed and refuse first-boot startup rather than inferring a broader or less safe environment.

## 7. Migration Bootstrap Contract

Migration bootstrap is part of the first-boot contract because the control-plane runtime is not allowed to treat an unverified PostgreSQL schema as implicitly ready.

The reviewed migration asset home remains `postgres/control-plane/migrations/`.

First boot must run the reviewed forward migration set needed for the approved control-plane schema before the runtime is treated as ready to serve authoritative control-plane state.

Migration bootstrap success means the required reviewed migration set completes without error and leaves the control-plane schema at the expected first-boot revision.

Migration bootstrap failure includes missing migration assets, a PostgreSQL connection failure, an unapplied required migration, a partially applied migration set, or any schema mismatch that would make authoritative control-plane writes ambiguous.

If migration bootstrap cannot prove the expected reviewed schema state, the deployment entrypoint must fail closed and refuse normal runtime startup.

Phase 16 does not approve automatic destructive repair, downgrade behavior, or ad hoc schema recreation as a first-boot fallback.

## 8. Healthcheck and Readiness Contract

The first-boot runtime contract requires a narrow distinction between process liveness and readiness for authoritative control-plane work.

Healthcheck success means the control-plane process is running and can answer a minimal self-health probe without asserting that dependencies are ready.

Readiness success means the control-plane runtime has loaded valid required bootstrap environment, can reach PostgreSQL through `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`, and has confirmed migration bootstrap success for the approved first-boot schema state.

Readiness must not depend on optional OpenSearch, n8n, Shuffle, or isolated-executor connectivity during the first-boot scope.

If the runtime cannot prove required bootstrap state, PostgreSQL reachability, or reviewed migration completion, readiness must fail closed.

The reverse proxy and any repository-local deployment surface must treat readiness failure as a refusal to admit normal traffic to the control-plane runtime.

## 9. Deployment-Entrypoint Contract

Any repository-local deployment entrypoint for first boot, including future Compose-backed bring-up, must preserve the approved control-plane, PostgreSQL, and reverse-proxy boundary instead of introducing a broader runtime dependency set.

The deployment entrypoint must supply the reviewed required bootstrap environment, execute migration bootstrap before declaring readiness, and stop startup if the migration contract or readiness contract is not satisfied.

The deployment entrypoint must not treat direct backend port publication, optional substrate availability, or placeholder repository defaults as acceptable substitutes for the approved first-boot contract.

Compose or other repository-local boot surfaces may orchestrate startup order, but they must not redefine first-boot success to require OpenSearch, n8n, the analyst-assistant surface, or executor availability.

Phase 16 therefore approves deployment-entrypoint expectations, not concrete image build details, health endpoint implementation, or live deployment automation.

## 10. Boundary and Alignment Notes

`docs/control-plane-runtime-service-boundary.md` remains the normative source for the live control-plane ownership split and repository placement.

`docs/architecture.md` remains the normative source for the separation between detection, control, automation, and execution.

`docs/network-exposure-and-access-path-policy.md` remains the normative source for the reverse proxy and internal exposure rules that first boot must preserve.

`docs/storage-layout-and-mount-policy.md` remains the normative source for persistent storage separation, including the distinction between PostgreSQL-owned state and optional substrate-local data.

`docs/compose-skeleton-overview.md` remains the normative source for the placeholder-safe status of repository-tracked compose assets before runtime implementation details are approved.

`README.md` remains aligned with this Phase 16 release-state by keeping OpenSearch and n8n optional and by keeping the control-plane runtime as the product authority boundary.
