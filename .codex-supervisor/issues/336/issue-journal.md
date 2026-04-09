# Issue #336: implementation: add CLI-first advisory inspection commands for cited assistant outputs

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/336
- Branch: codex/issue-336
- Workspace: .
- Journal: .codex-supervisor/issues/336/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: fe58835c9f6a15a556c483daef4065fbe78c11a3
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T10:37:42.070Z

## Latest Codex Summary
- Added CLI-first advisory inspection and recommendation-draft render commands on top of reviewed assistant-context snapshots, with focused CLI and service tests covering citation-preserving output.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Operators need a narrower CLI projection than `inspect-assistant-context`, specifically a cited advisory-output view and a recommendation-draft render that preserve reviewed anchors without exposing the full snapshot payload.
- What changed: Added `inspect-advisory-output` and `render-recommendation-draft` CLI commands, introduced service-level snapshot projections derived from `inspect_assistant_context`, and added focused CLI/service tests before widening to the full requested suites.
- Current blocker: none
- Next exact step: Commit the verified implementation checkpoint on `codex/issue-336`.
- Verification gap: none for the requested local suites; no PR/CI run yet.
- Files touched: control-plane/main.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_cli_inspection.py; control-plane/tests/test_service_persistence.py
- Rollback concern: Low; the new surface is read-only and reuses the existing assistant-context snapshot path rather than introducing a new query path.
- Last focused command: python3 -m unittest control-plane.tests.test_cli_inspection && python3 -m unittest control-plane.tests.test_service_persistence
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
