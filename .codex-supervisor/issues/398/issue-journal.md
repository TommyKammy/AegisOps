# Issue #398: validation: add end-to-end Phase 19 coverage for the approved operator workflow

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/398
- Branch: codex/issue-398
- Workspace: .
- Journal: .codex-supervisor/issues/398/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: c5dc4906a2b7bf02fa6c2d4384b0f5468516c3d1
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-12T03:32:36.473Z

## Latest Codex Summary
- Added a dedicated Phase 19 end-to-end runtime validator that drives the approved Wazuh-backed operator workflow over the reviewed HTTP surface, then wired the Phase 19 verifier, focused shell guard, CI workflow guard, and validation note to require that coverage.
- The first focused failure was an incorrect queue expectation in the new validator: before case promotion the queue review state is `pending_review`, not `case_required`. I corrected the test to assert the workflow in order by checking pre-promotion queue review first and post-promotion case-required state second.
- Full repository-local unittest discovery and the updated Phase 19 shell guards now pass.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 19 was missing a dedicated repository-local runtime validator for the approved operator workflow even though the underlying HTTP surface already supported the slice.
- What changed: Added `control-plane/tests/test_phase19_operator_workflow_validation.py` to exercise queue review, alert detail, case promotion, bounded casework actions, evidence provenance visibility, business-hours handoff/disposition, and cited advisory visibility over the reviewed runtime path. Updated the Phase 19 validation doc, verifier, shell self-test, CI workflow guard, and CI job command to require the new validator.
- Current blocker: none.
- Next exact step: Commit the Phase 19 validation checkpoint on `codex/issue-398`; open or update a draft PR if supervisor flow wants the checkpoint published early.
- Verification gap: none for the requested repository-local Phase 19 validation slice.
- Files touched: `.github/workflows/ci.yml`; `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md`; `scripts/verify-phase-19-thin-operator-surface.sh`; `scripts/test-verify-phase-19-thin-operator-surface.sh`; `scripts/test-verify-ci-phase-19-workflow-coverage.sh`; `control-plane/tests/test_phase19_operator_workflow_validation.py`.
- Rollback concern: The new validator encodes current reviewed runtime payload shapes for the first Wazuh-backed slice, so later operator-surface broadening will need intentional test updates rather than ad hoc drift.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
