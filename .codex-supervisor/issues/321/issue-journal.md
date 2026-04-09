# Issue #321: implementation: add analyst-assistant query surfaces over control-plane records, reviewed context, and linked evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/321
- Branch: codex/issue-321
- Workspace: .
- Journal: .codex-supervisor/issues/321/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 9 (implementation=1, repair=4)
- Last head SHA: 610e6e91fd0e7da68fc7d5c213cb39ae9f7af3fe
- Blocked reason: none
- Last failure signature: local-review:medium:none:1:0:clean
- Repeated failure signature count: 2
- Updated at: 2026-04-09T01:03:42.027Z

## Latest Codex Summary
Resolved the review thread by teaching reconciliation assistant snapshots to match sibling reconciliations through declared `subject_linkage["finding_ids"]` as well as the existing direct lineage surfaces. The fix lives in [`control-plane/aegisops_control_plane/service.py`](control-plane/aegisops_control_plane/service.py#L1233), with a focused regression added in [`control-plane/tests/test_service_persistence.py`](control-plane/tests/test_service_persistence.py#L784).

I also extended the reconciliation-context regression in [`control-plane/tests/test_service_persistence.py`](control-plane/tests/test_service_persistence.py#L784) so the assistant context now proves sibling reconciliation discovery via declared finding IDs.

Summary: Reconciliation assistant snapshots now resolve declared sibling finding linkage and preserve assistant-context coverage
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_matches_reconciliations_via_direct_action_linkage`; `python3 -m compileall aegisops_control_plane/service.py tests/test_service_persistence.py`; `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection`
Next action: commit the repair and wait for GitHub to re-evaluate PR `#327`
Failure signature: local-review:medium:none:1:0:clean

## Active Failure Context
- Category: blocked
- Summary: Local review found 1 actionable finding(s) across 1 root cause(s); max severity=medium; verified high-severity findings=0; verified max severity=none.
- Details:
  - findings=1
  - root_causes=1
  - summary=<redacted-local-path>

## Codex Working Notes
### Current Handoff
- Hypothesis: Reconciliation snapshots need to honor declared sibling finding linkage so assistant context does not miss reconciliations linked only through `subject_linkage["finding_ids"]`.
- What changed: `_assistant_reconciliation_records_for_context()` now matches sibling reconciliations against `subject_linkage["finding_ids"]`, and the reconciliation-context regression now covers a sibling record linked only by finding ID.
- Current blocker: None.
- Next exact step: create a checkpoint commit for the review fix.
- Verification gap: None for the changed behavior; the focused regression passed, the touched files compile, and `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection` passed from the `control-plane/` directory.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/321/issue-journal.md`.
- Rollback concern: The assistant-context surface is additive and read-only; reverting the new reconciliation linkage check and regression restores the prior inspection behavior.
- Last focused command: `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
