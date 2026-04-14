# Issue #459: implementation: split control-plane/tests/test_service_persistence.py into domain-focused regression modules

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/459
- Branch: codex/issue-459
- Workspace: .
- Journal: .codex-supervisor/issues/459/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: b9522dbbab870887ce17a447578d55d3b12fe755
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-14T04:07:54.998Z

## Latest Codex Summary
- Added a focused layout regression that requires persistence coverage to live in four domain modules.
- Split the former monolithic `test_service_persistence.py` into assistant/advisory, ingest/case lifecycle, action/reconciliation, and restore/readiness modules, with shared fixtures/helpers moved to `_service_persistence_support.py`.
- Updated `test_phase20_low_risk_action_validation.py` to validate the new action/reconciliation regression module instead of the retired monolith.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: A narrow topology test plus domain-focused modules can split the persistence suite without weakening regression coverage, and any validator coupled to the monolith must be repointed to the new domain files.
- What changed: Reduced `control-plane/tests/test_service_persistence.py` to helper/layout coverage, created `_service_persistence_support.py` for shared fixtures/helpers, added `test_service_persistence_assistant_advisory.py`, `test_service_persistence_ingest_case_lifecycle.py`, `test_service_persistence_action_reconciliation.py`, and `test_service_persistence_restore_readiness.py`, and repointed the phase-20 validation test to the action/reconciliation module.
- Current blocker: none.
- Next exact step: Stage the split persistence modules plus validation update and create a checkpoint commit on `codex/issue-459`.
- Verification gap: none for local discovery; full `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'` passes after the validation update.
- Files touched: `control-plane/tests/test_service_persistence.py`, `control-plane/tests/_service_persistence_support.py`, `control-plane/tests/test_service_persistence_assistant_advisory.py`, `control-plane/tests/test_service_persistence_ingest_case_lifecycle.py`, `control-plane/tests/test_service_persistence_action_reconciliation.py`, `control-plane/tests/test_service_persistence_restore_readiness.py`, `control-plane/tests/test_phase20_low_risk_action_validation.py`.
- Rollback concern: Low; the refactor is test-only, but `test_phase20_low_risk_action_validation.py` now depends on the new action/reconciliation module path.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
