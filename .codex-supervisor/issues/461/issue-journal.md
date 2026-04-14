# Issue #461: implementation: separate CLI command parsing from HTTP handler wiring in control-plane/main.py

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/461
- Branch: codex/issue-461
- Workspace: .
- Journal: .codex-supervisor/issues/461/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 040fb5575ca155669da8509a9f56bee7590db6fc
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-14T05:59:49.433Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: `control-plane/main.py` can be reduced to a thin entrypoint if CLI parsing/dispatch and HTTP handler wiring move into dedicated package modules, while `main.py` keeps small compatibility wrappers for existing tests and runtime callers.
- What changed: Added reproducing structural tests in `control-plane/tests/test_runtime_skeleton.py`; extracted shared entrypoint helpers into `control-plane/aegisops_control_plane/entrypoint_support.py`; moved CLI parser/dispatch into `control-plane/aegisops_control_plane/cli.py`; moved HTTP handler construction/runtime server wiring into `control-plane/aegisops_control_plane/http_surface.py`; reduced `control-plane/main.py` to wrapper entrypoints and compatibility shims.
- Current blocker: none
- Next exact step: commit the refactor and test additions on `codex/issue-461`; open/update draft PR only if requested in a later turn.
- Verification gap: focused verification passed; no broader suite run beyond `control-plane.tests.test_cli_inspection` and `control-plane.tests.test_runtime_skeleton`.
- Files touched: `control-plane/main.py`, `control-plane/aegisops_control_plane/entrypoint_support.py`, `control-plane/aegisops_control_plane/cli.py`, `control-plane/aegisops_control_plane/http_surface.py`, `control-plane/tests/test_runtime_skeleton.py`
- Rollback concern: low to moderate; the risk is wrapper compatibility around tests or any caller depending on removed `main.py` private helpers, mitigated by restoring `_read_json_file` and `_require_loopback_operator_request` shims in `main.py`.
- Last focused command: `python3 -m unittest control-plane.tests.test_cli_inspection control-plane.tests.test_runtime_skeleton`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
