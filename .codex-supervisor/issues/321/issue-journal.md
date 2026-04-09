# Issue #321: implementation: add analyst-assistant query surfaces over control-plane records, reviewed context, and linked evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/321
- Branch: codex/issue-321
- Workspace: .
- Journal: .codex-supervisor/issues/321/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 6 (implementation=1, repair=1)
- Last head SHA: 7469f8d9c00a2506e00d8499de7c0551c29b7620
- Blocked reason: none
- Last failure signature: local-review:medium:none:1:0:clean
- Repeated failure signature count: 2
- Updated at: 2026-04-09T00:41:51.697Z

## Latest Codex Summary
I updated the supervisor journal in the workspace, committed the fix as `7469f8d`, and pushed `codex/issue-321`.

The review fixes are in [`control-plane/aegisops_control_plane/service.py`](control-plane/aegisops_control_plane/service.py) and the regressions are in [`control-plane/tests/test_service_persistence.py`](control-plane/tests/test_service_persistence.py).

Summary: Fixed family-specific exclusion and subject-linkage reconciliation matching; added regressions and pushed `7469f8d`
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection` passed
Next action: Wait for GitHub to re-evaluate PR `#327` against `7469f8d`
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
- Hypothesis: Reconciliation snapshots need to seed linked alert/case/finding lineage from `subject_linkage["alert_ids"]` and resolved `subject_linkage["analytic_signal_ids"]`, not just top-level `alert_id`.
- What changed: `inspect_assistant_context()` now merges reconciliation subject-linkage alert IDs directly and resolves linked analytic signals back into alert, case, and finding lineage before reviewed-context aggregation and downstream matching.
- Current blocker: None.
- Next exact step: Commit the repair, then wait for GitHub to re-evaluate PR `#327`.
- Verification gap: None for the issue-specified control-plane persistence and CLI inspection suite; `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection` passed after the fix.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`.
- Rollback concern: The new assistant-context surface is additive and read-only; reverting the new CLI command and service method restores the prior inspection-only surface.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
