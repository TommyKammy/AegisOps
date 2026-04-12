# Issue #410: implementation: gate case-scoped assistant-context inspection to the approved Phase 19 operator slice

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/410
- Branch: codex/issue-410
- Workspace: .
- Journal: .codex-supervisor/issues/410/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: ab0c92a606fca85e9e9e6e12b652328d1a165edb
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-12T11:13:35.942Z

## Latest Codex Summary
- Added a fail-closed Phase 19 eligibility check at `inspect_assistant_context("case", ...)` so case-scoped assistant context now requires the approved Wazuh-backed GitHub audit live slice.
- Added focused in-scope and replay-only rejection coverage, then updated older case-scoped assistant/advisory/draft tests to use the reviewed Phase 19 in-scope fixture path instead of synthetic cases.
- Verified with focused `unittest` targets and a full `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'` run.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: `inspect_assistant_context("case", ...)` was bypassing the existing Phase 19 case-slice gate, so replay-only and other out-of-scope cases could still read case-scoped assistant context.
- What changed: Gated case-family assistant-context inspection through `_require_phase19_operator_case`, added focused service tests for accepted in-scope and rejected replay-only cases, and migrated existing case-scoped assistant/advisory/draft tests to the Phase 19 in-scope Wazuh GitHub audit fixture path.
- Current blocker: none
- Next exact step: Commit the verified checkpoint on `codex/issue-410`.
- Verification gap: none after full `control-plane/tests` discovery run.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_cli_inspection.py`, `.codex-supervisor/issues/410/issue-journal.md`
- Rollback concern: Low; behavior change is intentionally limited to `record_family == "case"` for assistant-context-derived case surfaces.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
