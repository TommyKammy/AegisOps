# Issue #321: implementation: add analyst-assistant query surfaces over control-plane records, reviewed context, and linked evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/321
- Branch: codex/issue-321
- Workspace: .
- Journal: .codex-supervisor/issues/321/issue-journal.md
- Current phase: addressing_review
- Attempt count: 9 (implementation=1, repair=4)
- Last head SHA: b9cadbb
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc55t6sY
- Repeated failure signature count: 1
- Updated at: 2026-04-09T00:58:20Z

## Latest Codex Summary
Resolved reconciliation assistant snapshots so action-lineage subject linkage now flows through alert, case, finding, and delegation-backed reconciliation matching before reviewed-context aggregation and downstream matching. The regression now covers the isolated-executor reconciliation path that actually carries delegation linkage.

Changed:
- [`control-plane/aegisops_control_plane/service.py`](/Users/jp.infra/Dev/AegisOps-worktrees/issue-321/control-plane/aegisops_control_plane/service.py) now hydrates reconciliation action lineage from `subject_linkage` and reuses it for linked-record selection.
- [`control-plane/tests/test_service_persistence.py`](/Users/jp.infra/Dev/AegisOps-worktrees/issue-321/control-plane/tests/test_service_persistence.py) now asserts isolated-executor reconciliation snapshots recover alert/case reviewed context and delegation-linked sibling reconciliations.

Verification:
- `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection`
- `python3 -m compileall aegisops_control_plane/service.py tests/test_service_persistence.py`

Summary: Reconciliation assistant snapshots now resolve action-lineage subject linkage and preserve delegation-backed sibling matching
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection`
Next action: wait for GitHub to re-evaluate PR `#327` against the new commit
Failure signature: PRRT_kwDOR2iDUc55t6sY

## Active Failure Context
- Category: review
- Summary: 1 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/327#discussion_r3054936646
- Details:
  - control-plane/aegisops_control_plane/service.py:812 summary=_⚠️ Potential issue_ | _🟠 Major_ **Resolve action-lineage from `ReconciliationRecord.subject_linkage` when the inspected record is itself a reconciliation.** These branches onl... url=https://github.com/TommyKammy/AegisOps/pull/327#discussion_r3054936646

## Codex Working Notes
### Current Handoff
- Hypothesis: Reconciliation snapshots need to resolve action-lineage IDs from `ReconciliationRecord.subject_linkage` so alert/case reviewed context and delegation-backed sibling matches are preserved.
- What changed: `inspect_assistant_context()` now hydrates `action_request_ids`, `approval_decision_ids`, `action_execution_ids`, and `delegation_ids` from reconciliation `subject_linkage` before selecting linked records, and `_assistant_reconciliation_records_for_context()` uses the same hydrated lineage for sibling matching.
- Current blocker: None.
- Next exact step: wait for GitHub to re-evaluate PR `#327` against the new commit.
- Verification gap: None for the issue-specified control-plane persistence and CLI inspection suite; `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection` passed from the `control-plane/` directory, and `python3 -m compileall aegisops_control_plane/service.py tests/test_service_persistence.py` passed.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/321/issue-journal.md`.
- Rollback concern: The new assistant-context surface is additive and read-only; reverting the new CLI command and service method restores the prior inspection-only surface.
- Last focused command: `python3 -m unittest tests.test_service_persistence tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
