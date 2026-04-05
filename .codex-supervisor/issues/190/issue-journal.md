# Issue #190: implementation: add read-only control-plane inspection for records and reconciliation status

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/190
- Branch: codex/issue-190
- Workspace: .
- Journal: .codex-supervisor/issues/190/issue-journal.md
- Current phase: draft_pr
- Attempt count: 2 (implementation=1, repair=1)
- Last head SHA: ad27a8a17b014af0dc83184a0efc925a4aaf71ed
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-05T02:53:38.107Z

## Latest Codex Summary
Added a bounded read-only inspection surface for the control-plane scaffold. The service now exposes record-family inspection and reconciliation-status snapshots in [service.py](control-plane/aegisops_control_plane/service.py), and [main.py](control-plane/main.py) now supports `inspect-records --family <family>` and `inspect-reconciliation-status` alongside the existing runtime snapshot. I also updated [test_service_persistence.py](control-plane/tests/test_service_persistence.py) and added [test_cli_inspection.py](control-plane/tests/test_cli_inspection.py) to lock the behavior in before and after the fix.

Committed on `codex/issue-190` as `098e54a` and `ad27a8a`, pushed the branch, and opened draft PR #199: https://github.com/TommyKammy/AegisOps/pull/199

Summary: Added read-only control-plane record inspection and reconciliation status views, with focused reproducing tests, CLI coverage, and a draft PR open.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_exposes_read_only_record_and_reconciliation_inspection`; `python3 -m unittest control-plane.tests.test_cli_inspection control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_exposes_read_only_record_and_reconciliation_inspection`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`; `rg -n "read-only|inspection|reconciliation" control-plane docs scripts`; `rg -n "alert|case|reconciliation" control-plane`
Next action: Hold on draft PR #199 for review feedback, or continue with follow-up polish if new scope is assigned.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The missing issue slice was a bounded read-only inspection surface; persisted control-plane records existed in the service/store boundary, but there was no service or CLI path to inspect them or summarize reconciliation state.
- What changed: Added a focused reproducing test for missing inspection methods, implemented read-only record-family and reconciliation-status snapshots in the control-plane service, exposed them via `control-plane/main.py` subcommands, added CLI coverage, updated the control-plane README to describe the read-only inspection path, committed the slice as `098e54a`, and opened draft PR #199.
- Current blocker: none
- Next exact step: Hold for review feedback on draft PR #199; current reported checks are green and there are no actionable review comments yet.
- Verification gap: No live PostgreSQL-backed inspection path exists yet; verification is limited to the in-memory control-plane scaffold and CLI/service tests.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/main.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_cli_inspection.py; control-plane/aegisops_control_plane/__init__.py; control-plane/README.md
- Rollback concern: Low; the new surface is read-only and additive, but callers relying on `main.py` always printing only the runtime snapshot now need to either keep the default command or pass an explicit subcommand.
- Last focused command: gh pr view 199 --json number,url,state,isDraft,reviewDecision,statusCheckRollup,comments,reviews
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
