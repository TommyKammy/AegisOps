# Issue #190: implementation: add read-only control-plane inspection for records and reconciliation status

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/190
- Branch: codex/issue-190
- Workspace: .
- Journal: .codex-supervisor/issues/190/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: a6565f6cae145a3c836a806a6e554435986b9a1a
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-05T02:45:14.438Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The missing issue slice was a bounded read-only inspection surface; persisted control-plane records existed in the service/store boundary, but there was no service or CLI path to inspect them or summarize reconciliation state.
- What changed: Added a focused reproducing test for missing inspection methods, implemented read-only record-family and reconciliation-status snapshots in the control-plane service, exposed them via `control-plane/main.py` subcommands, added CLI coverage, updated the control-plane README to describe the read-only inspection path, committed the slice as `098e54a`, and opened draft PR #199.
- Current blocker: none
- Next exact step: Hold for review feedback or continue with follow-up polish only if new scope appears.
- Verification gap: No live PostgreSQL-backed inspection path exists yet; verification is limited to the in-memory control-plane scaffold and CLI/service tests.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/main.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_cli_inspection.py; control-plane/aegisops_control_plane/__init__.py; control-plane/README.md
- Rollback concern: Low; the new surface is read-only and additive, but callers relying on `main.py` always printing only the runtime snapshot now need to either keep the default command or pass an explicit subcommand.
- Last focused command: python3 -m unittest discover -s control-plane/tests -p 'test_*.py'
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
