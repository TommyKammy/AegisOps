# Issue #304: implementation: add cross-signal correlation and enrichment paths for identity-rich alerts and cases

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/304
- Branch: codex/issue-304
- Workspace: .
- Journal: .codex-supervisor/issues/304/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 9b0be86002c00aa016ad91c4417085192c9b38e4
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-08T17:09:29.030Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: the analyst queue was omitting the normalized `reviewed_context`, so identity-rich Wazuh-backed alerts were still surfaced through reconciliation metadata but not through the shared control-plane vocabulary on the queue view.
- What changed: added `reviewed_context` to analyst queue records, and added focused service/CLI tests that assert Microsoft 365 audit alerts expose the normalized identity profile through `inspect_analyst_queue`.
- Current blocker: none.
- Next exact step: commit the service and test updates on `codex/issue-304`.
- Verification gap: focused unit coverage is green; no full repo sweep was run.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_cli_inspection.py`.
- Rollback concern: low; the queue payload change is additive and the tests only assert the new field is present and populated.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection` and `python3 -m unittest control-plane.tests.test_postgres_store`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
