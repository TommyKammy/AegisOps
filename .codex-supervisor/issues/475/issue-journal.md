# Issue #475: implementation: add pending / expired / rejected / superseded action-review surfaces to the operator workflow

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/475
- Branch: codex/issue-475
- Workspace: .
- Journal: .codex-supervisor/issues/475/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: aa508db389673b496a9618ee37c2dd42eee611af
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-14T13:09:48.154Z

## Latest Codex Summary
- Added reviewed action-review summaries to the existing queue, alert detail, and case detail surfaces so pending, expired, rejected, and superseded states remain inspectable inside AegisOps without implying execution success.
- Added focused coverage for pending rendering in the Phase 19 HTTP workflow test plus expired/rejected/superseded rendering in service and CLI inspection tests.

## Active Failure Context
- Reproduced before implementation: `inspect-analyst-queue` omitted `current_action_review` after creating a reviewed action request, leaving queue/alert/case surfaces unable to expose pending review state.

## Codex Working Notes
### Current Handoff
- Hypothesis: The repo already persisted approval/action lifecycle states, but the reviewed operator surfaces only rendered alerts/cases and generic record dumps, so operators could not inspect pending/expired/rejected/superseded action-review state from the primary workflow.
- What changed: Added a shared action-review chain summarizer in `control-plane/aegisops_control_plane/service.py`, surfaced `current_action_review` and `action_reviews` on queue/alert/case inspections, and added focused tests in Phase 19 workflow, reconciliation persistence, and CLI inspection coverage.
- Current blocker: none
- Next exact step: Commit the focused checkpoint on `codex/issue-475`; optionally open a draft PR from the branch if supervisor flow expects one immediately.
- Verification gap: Manual UI-style inspection was not performed beyond the existing HTTP/CLI inspection payload tests.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_phase19_operator_workflow_validation.py`, `control-plane/tests/test_service_persistence_action_reconciliation.py`, `control-plane/tests/test_cli_inspection.py`
- Rollback concern: The new queue/alert/case payload fields are additive, but downstream consumers that assumed no action-review payload may need to ignore the extra keys.
- Last focused command: `python3 -m unittest control-plane.tests.test_phase19_operator_workflow_validation control-plane.tests.test_service_persistence_action_reconciliation control-plane.tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
