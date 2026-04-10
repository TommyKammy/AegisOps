# Issue #365: implementation: make the control-plane runtime bootable through a reviewed image and compose-backed service path

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/365
- Branch: codex/issue-365
- Workspace: .
- Journal: .codex-supervisor/issues/365/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 9f49fcd9806b5256edee8e64b6f1ea62f5e7ff12
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T02:53:37.620Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The first-boot control-plane path was still only nominally bootable because Compose relied on `alpine`, repo bind mounts, and a mounted entrypoint instead of a reviewed runtime image artifact.
- What changed: Added a reviewed first-boot `Dockerfile`, switched the control-plane Compose service to `build` plus a tagged image, copied the runtime code and reviewed migrations into the image, added `AEGISOPS_CONTROL_PLANE_BOOT_MODE` and `AEGISOPS_CONTROL_PLANE_LOG_LEVEL` to the env contract, tightened entrypoint fail-closed validation, and added focused tests for the image-backed boot path.
- Current blocker: none
- Next exact step: Stage the reviewed artifact/test changes, create a checkpoint commit, and open or prepare a draft PR for branch `codex/issue-365`.
- Verification gap: No live `docker compose up` against a real PostgreSQL instance was run; validation covered unit tests, contract verifiers, compose rendering, and image build only.
- Files touched: control-plane/deployment/first-boot/Dockerfile; control-plane/deployment/first-boot/docker-compose.yml; control-plane/deployment/first-boot/control-plane-entrypoint.sh; control-plane/deployment/first-boot/bootstrap.env.sample; control-plane/tests/test_phase17_first_boot_runtime_artifacts.py; control-plane/tests/test_phase16_bootstrap_contract_docs.py; control-plane/tests/test_phase16_first_boot_verifier.py; scripts/verify-phase-16-first-boot-contract.sh
- Rollback concern: Reverting to the prior placeholder Compose path would restore repo bind-mount assumptions and drop the reviewed image artifact and stricter startup validation.
- Last focused command: docker build -f control-plane/deployment/first-boot/Dockerfile -t aegisops-control-plane:first-boot .
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
