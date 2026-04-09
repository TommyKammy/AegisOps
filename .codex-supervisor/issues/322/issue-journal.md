# Issue #322: implementation: deliver advisory-only AI triage summaries and recommendation drafts with citations to reviewed records and evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/322
- Branch: codex/issue-322
- Workspace: .
- Journal: .codex-supervisor/issues/322/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: af7c12defd84d55eb506d944c7d70ba2173408ea
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T01:19:47.051Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: assistant-context snapshots for recommendation and AI-trace records need to surface reviewed alert/case evidence explicitly, not just the local record payload, so advisory output can stay citation-first.
- What changed: added a regression test for citation-ready recommendation/AI-trace context; extended `inspect_assistant_context()` to retain cited alert/case records, merge reviewed context from linked recommendation lineage, and expose linked alert/case records in the snapshot payload.
- Current blocker: none.
- Next exact step: none; implementation and targeted verification are complete for this issue slice.
- Verification gap: full issue-specific acceptance is covered by the persistence test module, but no broader runtime or CI validation was run here.
- Files touched: `control-plane/tests/test_service_persistence.py`, `control-plane/aegisops_control_plane/service.py`.
- Rollback concern: the assistant-context payload is larger now because it includes linked alert/case records; if a downstream consumer assumes the previous JSON shape, it will need to tolerate the extra fields.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
