# Issue #293: implementation: keep mismatched execution observations from mutating authoritative action-execution state

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/293
- Branch: codex/issue-293
- Workspace: .
- Journal: .codex-supervisor/issues/293/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: b331bef5fcfc16bfcfcb4d69ae560ae11a42f6ed
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-07T21:25:04.383Z

## Latest Codex Summary
- Reproduced a fail-open reconciliation bug where a wrong-surface observed execution marked as `mismatch` still mutated the authoritative `ActionExecutionRecord` lifecycle from `queued` to `failed`.
- Added a focused regression test and fixed `reconcile_action_execution` so authoritative execution lifecycle transitions only occur for `matched` observations.
- Verified with the named focused reconciliation tests and the full `control-plane/tests` suite.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The reconciliation path was updating authoritative execution lifecycle state whenever any latest observation existed, even if reconciliation classified that observation as non-authoritative (`mismatch`, `duplicate`, `stale`).
- What changed: Added a focused regression test for wrong-surface mismatch behavior and gated authoritative `ActionExecutionRecord` lifecycle mutation on `ingest_disposition == "matched"` inside `reconcile_action_execution`.
- Current blocker: none
- Next exact step: Commit the tested fix on `codex/issue-293`; branch is ready for the next supervisor phase.
- Verification gap: None in local tests; focused regression and full test discovery both pass.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/293/issue-journal.md`
- Rollback concern: Low; change only narrows when authoritative execution state may be mutated and leaves reconciliation record creation intact.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
