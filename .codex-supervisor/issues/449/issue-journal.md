# Issue #449: follow-up: stop treating break-glass as a mandatory Phase 21 startup binding when the reviewed design keeps it disabled by default

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/449
- Branch: codex/issue-449
- Workspace: .
- Journal: .codex-supervisor/issues/449/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 0509c6a7c559721d4ce87966ca764770b985212d
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-13T22:34:43.246Z

## Latest Codex Summary
- Reproduced the Phase 21 startup/readiness defect with a focused runtime-auth service test showing `startup_ready=False` when break-glass is intentionally unset.
- Fixed `describe_startup_status()` so break-glass is no longer treated as a mandatory startup binding while keeping admin bootstrap and other reviewed required bindings intact.
- Extended runtime-auth coverage to prove the break-glass contract still fails closed when disabled by default and when a wrong token is supplied.
- Verified the fix with focused runtime-auth, CLI inspection, end-to-end, and Phase 21 boundary validation suites.
- Published commit `8b3f5c4` to `origin/codex/issue-449` and opened draft PR `#451`.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: `describe_startup_status()` was incorrectly including `AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN` in `required_bindings`, which forced readiness to fail closed even though the reviewed design keeps break-glass disabled by default until explicitly configured.
- What changed: Removed break-glass from the mandatory startup binding tuple in `control-plane/aegisops_control_plane/service.py`; added a focused service test proving startup/readiness stay healthy with PostgreSQL, Wazuh ingest, and admin bootstrap configured but break-glass unset; added direct tests proving break-glass still rejects use when disabled and when a wrong token is supplied.
- Current blocker: none
- Next exact step: Monitor draft PR `#451` and address any review or CI feedback.
- Verification gap: Did not run the full repository test suite; focused Phase 21 runtime-auth, CLI, end-to-end, and boundary validation coverage passed.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_phase21_runtime_auth_validation.py`, `.codex-supervisor/issues/449/issue-journal.md`
- Rollback concern: Low; change is limited to startup/readiness semantics and does not alter break-glass activation enforcement.
- Last focused command: `gh pr create --draft --title "[codex] Fix phase 21 startup break-glass readiness" --body-file "$tmpfile" --base main --head codex/issue-449`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproducing test failure before fix: `python3 -m unittest control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_startup_and_readiness_do_not_require_break_glass_when_unset` -> `AssertionError: False is not true`
