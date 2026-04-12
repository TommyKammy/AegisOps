# Issue #411: implementation: fail closed advisory-output and recommendation-draft reads for out-of-scope Phase 19 cases

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/411
- Branch: codex/issue-411
- Workspace: .
- Journal: .codex-supervisor/issues/411/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 531c23244e1b4e69ceda7cb8931f65f3d15cc401
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-12T11:47:34.960Z

## Latest Codex Summary
- Added a Phase 19 case-scope guard to `inspect_advisory_output(...)` and `render_recommendation_draft(...)` so advisory reads fail closed when the requested record is a case or links to a case outside the approved Wazuh-backed GitHub audit live slice.
- Added focused service, CLI, and HTTP tests covering rejected replay-linked `recommendation`/`ai_trace` advisory reads while keeping accepted in-scope case reads green.
- Rebased older recommendation-draft and advisory-draft attachment tests onto the existing in-scope Phase 19 fixture so lifecycle and attachment coverage stays on the approved slice.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The fail-open path was not the direct `family=case` read, but advisory reads for `recommendation` and `ai_trace` records that inherited scope from replay-only cases because only `inspect_assistant_context(..., family=\"case\")` enforced the Phase 19 slice gate.
- What changed: Added `_require_phase19_case_scoped_advisory_read(...)` and invoked it from `inspect_advisory_output(...)` and `render_recommendation_draft(...)`; added focused rejection tests for replay-linked review records on service/CLI/HTTP paths; updated older advisory-draft lifecycle tests to use the approved in-scope Phase 19 fixture.
- Current blocker: none
- Next exact step: Commit the local changes on `codex/issue-411`; PR creation can follow from this checkpoint if needed.
- Verification gap: none from local suite; full `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'` passed.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_cli_inspection.py`, `.codex-supervisor/issues/411/issue-journal.md`
- Rollback concern: The new guard intentionally narrows advisory reads for review records linked to out-of-scope cases; older non-Phase-19 advisory-draft tests were updated to keep approved-slice behavior explicit.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
