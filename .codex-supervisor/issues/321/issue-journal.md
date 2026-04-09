# Issue #321: implementation: add analyst-assistant query surfaces over control-plane records, reviewed context, and linked evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/321
- Branch: codex/issue-321
- Workspace: .
- Journal: .codex-supervisor/issues/321/issue-journal.md
- Current phase: stabilizing
- Attempt count: 10 (implementation=1, repair=5)
- Last head SHA: fb94563de20adb9cb9af4b30206af1e7b7f1fed7
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T01:09:23.221Z

## Latest Codex Summary
Added reconciliation sibling matching for declared `subject_linkage["finding_ids"]`, covered it with a regression in `control-plane/tests/test_service_persistence.py`, and committed the fix as `fb94563`.

Summary: Reconciliation assistant context now includes sibling reconciliations linked only through declared finding IDs
State hint: stabilizing
Blocked reason: none
Tests: `python3 -m unittest tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_matches_reconciliations_via_direct_action_linkage`; `python3 -m compileall aegisops_control_plane/service.py tests/test_service_persistence.py`; `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection`
Next action: wait for GitHub to re-evaluate PR `#327`
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Reconciliation snapshots need to honor declared sibling finding linkage so assistant context does not miss reconciliations linked only through `subject_linkage["finding_ids"]`.
- What changed: `_assistant_reconciliation_records_for_context()` now matches sibling reconciliations against `subject_linkage["finding_ids"]`, and the reconciliation-context regression now covers a sibling record linked only by finding ID.
- Current blocker: None.
- Next exact step: wait for GitHub to re-evaluate PR `#327` against commit `fb94563`.
- Verification gap: None for the changed behavior; the focused regression passed, the touched files compile, and `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection` passed from the `control-plane/` directory.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/321/issue-journal.md`.
- Rollback concern: The assistant-context surface is additive and read-only; reverting the new reconciliation linkage check and regression restores the prior inspection behavior.
- Last focused command: `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
