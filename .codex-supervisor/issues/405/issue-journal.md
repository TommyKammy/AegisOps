# Issue #405: follow-up: fail closed instead of crashing on lead-only advisory rendering

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/405
- Branch: codex/issue-405
- Workspace: .
- Journal: .codex-supervisor/issues/405/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 77491074d5e3a0a72d29af9cbda1c092c8efb34f
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-12T07:53:06.292Z

## Latest Codex Summary
- Reproduced the lead-only recommendation crash with a focused persistence test that persists a valid `lead_id` but omits direct `alert_id` and `case_id`, then calls `render_recommendation_draft()`.
- Fixed `_build_assistant_advisory_output()` so advisory status is computed independently of direct alert/case linkage, which preserves fail-closed `unresolved` output instead of raising `UnboundLocalError`.
- Verified with `python3 -m unittest control-plane.tests.test_service_persistence` and `python3 -m unittest control-plane.tests.test_cli_inspection`.

## Active Failure Context
- Resolved: `UnboundLocalError: local variable 'status' referenced before assignment` in `_build_assistant_advisory_output()` for lead-only recommendation rendering.

## Codex Working Notes
### Current Handoff
- Hypothesis: Lead-only reviewed recommendations bypass direct alert/case linkage, so the advisory builder must set `status` without assuming `linked_alert_ids` or `linked_case_ids` are present.
- What changed: Added a focused regression test for a valid lead-linked recommendation with no direct alert/case lineage and moved advisory `status` assignment outside the alert/case observation branch.
- Current blocker: none
- Next exact step: Commit the bounded fix on `codex/issue-405`.
- Verification gap: none for the scoped change; focused reproducer, full persistence suite, and CLI inspection suite all pass locally.
- Files touched: `control-plane/tests/test_service_persistence.py`, `control-plane/aegisops_control_plane/service.py`
- Rollback concern: Low; the code change only decouples status initialization from alert/case linkage while leaving fail-closed checks and advisory text selection intact.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
