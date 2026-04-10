# Phase 17 Runtime Config Contract and Boot Command Validation

- Validation date: 2026-04-10
- Validation scope: Phase 17 review of the approved first-boot runtime config contract, required and optional environment keys, reviewed defaults, fail-closed boot behavior, migration-bootstrap sequencing, reverse-proxy-only exposure expectations, and explicit Phase 16-to-Phase 17 carry-forward boundaries
- Baseline references: `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/control-plane-runtime-service-boundary.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, `README.md`
- Verification commands: `bash scripts/verify-phase-17-runtime-config-contract.sh`, `bash scripts/test-verify-phase-17-runtime-config-contract.sh`
- Validation status: PASS

## Required Boundary Artifacts

- `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`
- `docs/phase-17-runtime-config-contract-validation.md`
- `docs/phase-16-release-state-and-first-boot-scope.md`
- `docs/control-plane-runtime-service-boundary.md`
- `docs/network-exposure-and-access-path-policy.md`
- `docs/storage-layout-and-mount-policy.md`
- `README.md`
- `scripts/verify-phase-17-runtime-config-contract.sh`
- `scripts/test-verify-phase-17-runtime-config-contract.sh`

## Review Outcome

Confirmed the Phase 17 contract makes the approved first-boot runtime environment keys explicit enough to drive image, Compose, and entrypoint implementation without reopening the approved runtime floor.

Confirmed `AEGISOPS_CONTROL_PLANE_HOST`, `AEGISOPS_CONTROL_PLANE_PORT`, `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`, `AEGISOPS_CONTROL_PLANE_BOOT_MODE`, and `AEGISOPS_CONTROL_PLANE_LOG_LEVEL` are the approved required first-boot runtime keys and that startup must fail closed when they are absent, empty, malformed, contradictory, or exposure-bypassing.

Confirmed the reviewed local defaults stay narrow by allowing `127.0.0.1`, `8080`, `first-boot`, and `INFO` while keeping `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` without a repository default.

Confirmed the Phase 17 contract keeps `AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL`, `AEGISOPS_CONTROL_PLANE_N8N_BASE_URL`, `AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL`, and `AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL` explicitly optional and non-blocking for the first-boot path.

Confirmed the approved boot command shape keeps migration bootstrap in the normal first-boot path by requiring runtime-config validation, migration-asset validation, PostgreSQL reachability proof, forward migration application, schema-state verification, and only then `exec` of the control-plane service process.

Confirmed migration bootstrap failure remains fail-closed when reviewed migration assets are missing, PostgreSQL is unreachable, a forward migration fails, required migrations are only partially applied, or the expected reviewed schema state cannot be proven after execution.

Confirmed the reverse proxy remains the only approved user-facing ingress path and that repository-local boot surfaces must not publish the control-plane backend port directly to user networks or the public internet.

Confirmed the Phase 17 contract turns the reviewed Phase 16 first-boot skeleton environment keys, entrypoint sequencing, migration-home requirement, liveness-versus-readiness distinction, and reverse-proxy-first access model into concrete runtime expectations without making OpenSearch, n8n, Shuffle, executor wiring, thin UI work, or destructive schema shortcuts part of initial bring-up.

The issue requested review against `Phase 16-21 Epic Roadmap.md`, but that roadmap file was not present in the local worktree and could not be located via repository search during this turn.

## Cross-Link Review

`docs/phase-16-release-state-and-first-boot-scope.md` must continue to define the approved first-boot runtime floor that Phase 17 implements concretely rather than broadening.

`docs/control-plane-runtime-service-boundary.md` must continue to keep the control-plane service as the AegisOps-owned runtime authority boundary for image and entrypoint work.

`docs/network-exposure-and-access-path-policy.md` must continue to keep the reverse proxy as the approved ingress boundary and disallow direct backend publication as a substitute.

`docs/storage-layout-and-mount-policy.md` must continue to keep PostgreSQL state ownership and reviewed mount expectations distinct from optional substrate storage.

`README.md` must continue to describe the Phase 16 first-boot target as the approved floor for Phase 17 bring-up and keep optional substrates out of the product-core runtime baseline.

## Deviations

- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.
