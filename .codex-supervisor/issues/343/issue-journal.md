# Issue #343: follow-up: reflect current review outcome in recommendation-draft rendering

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/343
- Branch: codex/issue-343
- Workspace: .
- Journal: .codex-supervisor/issues/343/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 9883b1b60ad7776bcbd0b2922b39860023881d9c
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T11:45:27.391Z

## Latest Codex Summary
- Added focused service and CLI coverage proving recommendation-draft rendering was hardcoded to "remains under review" even after the source Recommendation or AI Trace lifecycle moved to accepted or rejected-for-reference.
- Updated recommendation-draft rendering to derive its cited summary from the source record's current lifecycle state and exposed `review_lifecycle_state` in the rendered draft payload without changing advisory ready/unresolved semantics.
- Verified with focused reproduction tests plus the full `test_service_persistence` and `test_cli_inspection` suites.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Recommendation-draft rendering was reading current linkage and citations but using a fixed under-review summary string, so accepted/rejected review records still rendered as pending review.
- What changed: Added narrow regression tests for service and CLI rendering on recommendation/ai_trace families; introduced lifecycle-aware recommendation-draft summary text; added rendered `review_lifecycle_state` to the draft payload.
- Current blocker: none
- Next exact step: Commit the verified fix on `codex/issue-343` and leave the branch ready for review or PR creation.
- Verification gap: none for the requested persistence and CLI suites.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_cli_inspection.py; .codex-supervisor/issues/343/issue-journal.md
- Rollback concern: Low; change is limited to recommendation-draft rendering text/payload and focused test coverage.
- Last focused command: python3 -m unittest control-plane.tests.test_cli_inspection
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
