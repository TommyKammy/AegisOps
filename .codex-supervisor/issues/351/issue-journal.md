# Issue #351: implementation: add first-boot bootstrap artifacts and deployment-entrypoint skeletons for the approved scope

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/351
- Branch: codex/issue-351
- Workspace: .
- Journal: .codex-supervisor/issues/351/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: 9c0ad3e2bc3a2fe32b61b6943f7e7b5bc15e3457
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T15:10:40.566Z

## Latest Codex Summary
Added the Phase 16 first-boot artifact slice under [control-plane/deployment/first-boot/bootstrap.env.sample](control-plane/deployment/first-boot/bootstrap.env.sample), [control-plane/deployment/first-boot/docker-compose.yml](control-plane/deployment/first-boot/docker-compose.yml), and [control-plane/deployment/first-boot/control-plane-entrypoint.sh](control-plane/deployment/first-boot/control-plane-entrypoint.sh). The sample keeps `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` explicit, the compose skeleton stays limited to control-plane/PostgreSQL/proxy, and the entrypoint validates only the required first-boot contract while marking OpenSearch, n8n, assistant UI, and executor wiring as deferred.

I tightened [control-plane/tests/test_phase16_bootstrap_contract_docs.py](control-plane/tests/test_phase16_bootstrap_contract_docs.py) to reproduce the missing-artifact failure first, then verified the new skeletons. I also added a short pointer in [control-plane/README.md](control-plane/README.md), pushed branch `codex/issue-351`, and opened draft PR `#356` at `https://github.com/TommyKammy/AegisOps/pull/356`. PR creation through the GitHub app connector failed with `Resource not accessible by integration`, so the PR was opened via `gh pr create --draft` instead.

Summary: Added Phase 16 first-boot bootstrap sample and deployment-entrypoint skeletons under `control-plane/deployment/first-boot/`, tightened the focused contract test, and committed the checkpoint as `9c0ad3e`.
State hint: local_review
Blocked reason: none
Tests: `python3 -m unittest control-plane/tests/test_phase16_bootstrap_contract_docs.py`; `python3 -m unittest control-plane/tests/test_runtime_skeleton.py`; `bash scripts/verify-phase-16-release-state-and-first-boot-scope.sh`; `bash scripts/test-verify-phase-16-release-state-and-first-boot-scope.sh`; `bash scripts/verify-control-plane-runtime-skeleton.sh`
Next action: Review the committed skeleton artifacts, then open or update the draft PR for issue #351 if this checkpoint is acceptable
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The implementation is stable and the remaining work is review-driven; no broader runtime expansion is needed unless PR feedback identifies a real contract gap.
- What changed: Pushed `codex/issue-351` to `origin`, confirmed no existing PR, attempted connector-based PR creation, then opened draft PR `#356` via `gh` after the GitHub app returned `Resource not accessible by integration`.
- Current blocker: none
- Next exact step: Keep PR `#356` in draft for local review and address any feedback without widening beyond the approved Phase 16 skeletal scope.
- Verification gap: No live container bring-up was attempted because the approved scope is skeletal and explicitly excludes real runtime image implementation and live secret distribution; PR creation required `gh` fallback because the GitHub app lacked permission to create PRs here.
- Files touched: `control-plane/tests/test_phase16_bootstrap_contract_docs.py`, `control-plane/README.md`, `control-plane/deployment/first-boot/bootstrap.env.sample`, `control-plane/deployment/first-boot/docker-compose.yml`, `control-plane/deployment/first-boot/control-plane-entrypoint.sh`, `.codex-supervisor/issues/351/issue-journal.md`
- Rollback concern: Low; new files are additive skeleton assets and the only existing-file changes are a README note and a focused repository-contract test.
- Last focused command: `gh pr create --draft --base main --head codex/issue-351 --title "[codex] Add Phase 16 first-boot bootstrap skeletons" --body-file "$tmp_body"`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced initial failure with `python3 -m unittest control-plane/tests/test_phase16_bootstrap_contract_docs.py` before adding artifacts; missing path was `control-plane/deployment/first-boot/bootstrap.env.sample`.
- Draft PR URL: `https://github.com/TommyKammy/AegisOps/pull/356`
