# Issue #293: implementation: keep mismatched execution observations from mutating authoritative action-execution state

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/293
- Branch: codex/issue-293
- Workspace: .
- Journal: .codex-supervisor/issues/293/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: cb4d7a386dc073cda784422bfa6b3b1064a09b38
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-07T21:30:11.863Z

## Latest Codex Summary
Implemented the fix in [service.py](control-plane/aegisops_control_plane/service.py#L1334) so authoritative `ActionExecutionRecord` lifecycle updates only happen for `matched` observations. Non-authoritative reconciliation outcomes still produce explicit `ReconciliationRecord`s, but they no longer promote wrong-surface observations into execution truth.

Added a focused regression test in [test_service_persistence.py](control-plane/tests/test_service_persistence.py#L1929) that reproduces the issue: a wrong-surface observation returns `mismatch` while the stored authoritative execution remains `queued`. The issue journal was updated at [.codex-supervisor/issues/293/issue-journal.md](.codex-supervisor/issues/293/issue-journal.md). Checkpoint commit: `cb4d7a3` (`Guard authoritative execution reconciliation state`).

Summary: Guarded authoritative execution lifecycle mutation behind `matched` reconciliation only, added a reproducing regression test, updated the issue journal, and committed the fix.
State hint: implementing
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciliation_mismatch_does_not_mutate_authoritative_execution`; `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_records_execution_correlation_mismatch_states_separately control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_shuffle_run_back_into_authoritative_action_execution control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
Next action: Open or update a draft PR for `codex/issue-293`, then move supervisor state from reproducing to the next implementation/review phase.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The reconciliation path was updating authoritative execution lifecycle state whenever any latest observation existed, even if reconciliation classified that observation as non-authoritative (`mismatch`, `duplicate`, `stale`).
- What changed: Added a focused regression test for wrong-surface mismatch behavior and gated authoritative `ActionExecutionRecord` lifecycle mutation on `ingest_disposition == "matched"` inside `reconcile_action_execution`.
- Current blocker: none
- Next exact step: Push `codex/issue-293` to a branch-specific remote ref and open a draft PR for review.
- Verification gap: None in local tests; focused regression and full test discovery both pass.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/293/issue-journal.md`
- Rollback concern: Low; change only narrows when authoritative execution state may be mutated and leaves reconciliation record creation intact.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
- 2026-04-07T21:31:02Z verification refresh: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_records_execution_correlation_mismatch_states_separately control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_shuffle_run_back_into_authoritative_action_execution control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution`; `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciliation_mismatch_does_not_mutate_authoritative_execution`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
