# Issue #351: implementation: add first-boot bootstrap artifacts and deployment-entrypoint skeletons for the approved scope

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/351
- Branch: codex/issue-351
- Workspace: .
- Journal: .codex-supervisor/issues/351/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: a7ddd4c956ec25a1355c7e4b51c654b2a03eec9c
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T15:02:56.173Z

## Latest Codex Summary
- Added repository-local Phase 16 first-boot bootstrap artifacts and deployment-entrypoint skeletons under `control-plane/deployment/first-boot/`, and tightened the focused Phase 16 contract test to require them and keep deferred components explicit.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The current Phase 16 gap is not runtime behavior but missing repository-local first-boot artifacts, so the narrowest reproducible failure is a contract test that expects a bootstrap sample and entrypoint skeletons under the approved `control-plane/` runtime home.
- What changed: Added a focused failing test in `control-plane/tests/test_phase16_bootstrap_contract_docs.py`, reproduced the failure for the missing bootstrap sample, then added `control-plane/deployment/first-boot/bootstrap.env.sample`, `control-plane/deployment/first-boot/docker-compose.yml`, `control-plane/deployment/first-boot/control-plane-entrypoint.sh`, and a small `control-plane/README.md` note documenting the new scaffold home.
- Current blocker: none
- Next exact step: Stage the focused Phase 16 artifact changes, create a checkpoint commit on `codex/issue-351`, and leave the branch ready for local review or draft PR creation.
- Verification gap: No live container bring-up was attempted because the approved scope is skeletal and explicitly excludes real runtime image implementation and live secret distribution.
- Files touched: `control-plane/tests/test_phase16_bootstrap_contract_docs.py`, `control-plane/README.md`, `control-plane/deployment/first-boot/bootstrap.env.sample`, `control-plane/deployment/first-boot/docker-compose.yml`, `control-plane/deployment/first-boot/control-plane-entrypoint.sh`
- Rollback concern: Low; new files are additive skeleton assets and the only existing-file changes are a README note and a focused repository-contract test.
- Last focused command: `bash scripts/test-verify-phase-16-release-state-and-first-boot-scope.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced initial failure with `python3 -m unittest control-plane/tests/test_phase16_bootstrap_contract_docs.py` before adding artifacts; missing path was `control-plane/deployment/first-boot/bootstrap.env.sample`.
