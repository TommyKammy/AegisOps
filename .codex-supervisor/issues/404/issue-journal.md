# Issue #404: follow-up: expose cited advisory review routes on the Phase 19 runtime surface

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/404
- Branch: codex/issue-404
- Workspace: .
- Journal: .codex-supervisor/issues/404/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: c1fc55eeaa7647aa5855a316ed4f942f4597c08d
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-12T08:20:26.406Z

## Latest Codex Summary
- Added the three cited advisory review GET routes to the long-running runtime surface and aligned their `400`/`404` handling with the existing reviewed inspection routes.
- Added a focused HTTP reproducer in `control-plane/tests/test_cli_inspection.py` and extended the Phase 19 workflow validation to exercise the advisory review reads over runtime HTTP.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The CLI advisory inspection commands already worked, but `run_control_plane_service()` never routed `/inspect-assistant-context`, `/inspect-advisory-output`, or `/render-recommendation-draft`, so runtime callers fell through to generic route-level `404 not_found`.
- What changed: Added reviewed GET handlers for the three advisory routes in `control-plane/main.py`, preserving read-only behavior and mapping missing `family`/`record_id` to `400`, `ValueError` to `400`, and `LookupError` to `404`. Added a focused runtime regression test in `control-plane/tests/test_cli_inspection.py` and extended `control-plane/tests/test_phase19_operator_workflow_validation.py` to exercise the advisory review reads.
- Current blocker: none.
- Next exact step: Commit the runtime route and test changes on `codex/issue-404`, then hand back with the focused verification results.
- Verification gap: Did not run the entire repository test suite; focused verification covered `control-plane.tests.test_cli_inspection` and `control-plane.tests.test_phase19_operator_workflow_validation`.
- Files touched: `control-plane/main.py`, `control-plane/tests/test_cli_inspection.py`, `control-plane/tests/test_phase19_operator_workflow_validation.py`.
- Rollback concern: Low; changes are limited to read-only GET routing and test coverage, with no operator write-path or auth-boundary expansion.
- Last focused command: `python3 -m unittest control-plane.tests.test_cli_inspection control-plane.tests.test_phase19_operator_workflow_validation`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
