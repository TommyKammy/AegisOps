# Issue #343: follow-up: reflect current review outcome in recommendation-draft rendering

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/343
- Branch: codex/issue-343
- Workspace: .
- Journal: .codex-supervisor/issues/343/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: 6ebf610e214b5ed09a13b9bdebdcef8bcd4d30c4
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T11:52:10.654Z

## Latest Codex Summary
Updated recommendation-draft rendering so source `Recommendation` and `AI Trace` records now reflect their current review outcome instead of always saying under review. The render path now emits lifecycle-aware summary text and includes an explicit `review_lifecycle_state` field while keeping the existing advisory `status` semantics unchanged in [service.py](control-plane/aegisops_control_plane/service.py#L474) and [service.py](control-plane/aegisops_control_plane/service.py#L758).

I added focused regression coverage for accepted and rejected outcomes in the practical service and CLI render paths in [test_service_persistence.py](control-plane/tests/test_service_persistence.py#L786) and [test_cli_inspection.py](control-plane/tests/test_cli_inspection.py#L494). I also updated the issue journal and committed the change as `6ebf610` (`Reflect review outcome in recommendation drafts`).

Summary: Recommendation-draft rendering now reflects accepted/rejected source review outcomes and exposes `review_lifecycle_state`; focused service and CLI regressions were added and all requested tests pass.
State hint: local_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_renders_recommendation_draft_with_current_review_outcome`; `python3 -m unittest control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_cli_renders_recommendation_draft_with_source_review_outcome`; `python3 -m unittest control-plane.tests.test_service_persistence`; `python3 -m unittest control-plane.tests.test_cli_inspection`
Next action: Open or update a draft PR for `codex/issue-343` if the supervisor wants branch review next.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Recommendation-draft rendering was reading current linkage and citations but using a fixed under-review summary string, so accepted/rejected review records still rendered as pending review.
- What changed: Added narrow regression tests for service and CLI rendering on recommendation/ai_trace families; introduced lifecycle-aware recommendation-draft summary text; added rendered `review_lifecycle_state` to the draft payload; committed the fix as `6ebf610`.
- Current blocker: none
- Next exact step: Open or update a draft PR for `codex/issue-343`, or hand the branch to review if PR creation is being handled elsewhere.
- Verification gap: none for the requested persistence and CLI suites; reran the focused CLI regression while stabilizing.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_cli_inspection.py; .codex-supervisor/issues/343/issue-journal.md
- Rollback concern: Low; change is limited to recommendation-draft rendering text/payload and focused test coverage.
- Last focused command: python3 -m unittest control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_cli_renders_recommendation_draft_with_source_review_outcome
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
