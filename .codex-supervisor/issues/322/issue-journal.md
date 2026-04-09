# Issue #322: implementation: deliver advisory-only AI triage summaries and recommendation drafts with citations to reviewed records and evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/322
- Branch: codex/issue-322
- Workspace: .
- Journal: .codex-supervisor/issues/322/issue-journal.md
- Current phase: addressing_review
- Attempt count: 3 (implementation=2, repair=1)
- Last head SHA: 71ae63fe2b95f1f5fea8ec5f2f27f0675a839f50
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc55uOxF|PRRT_kwDOR2iDUc55uOxG|PRRT_kwDOR2iDUc55uOxH
- Repeated failure signature count: 1
- Updated at: 2026-04-09T01:39:58.945Z

## Latest Codex Summary
Summary: Published `codex/issue-322` to GitHub and opened draft PR #328 (`https://github.com/TommyKammy/AegisOps/pull/328`) for the citation-ready advisory triage checkpoint; the local issue journal was refreshed with the PR handoff note.
State hint: pr_open
Blocked reason: none
Tests: not run this turn; prior persistence verification remains recorded in the issue journal
Next action: watch PR #328 for CI/review, and decide whether to keep the journal update local or commit it separately
Failure signature: PRRT_kwDOR2iDUc55uOxF|PRRT_kwDOR2iDUc55uOxG|PRRT_kwDOR2iDUc55uOxH

## Active Failure Context
- Category: review
- Summary: 3 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/328#discussion_r3055047785
- Details:
  - .codex-supervisor/issues/322/issue-journal.md:8 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Clarify the current phase status.** The "Current phase: reproducing" conflicts with line 27's statement that "implementation and targeted ver... url=https://github.com/TommyKammy/AegisOps/pull/328#discussion_r3055047785
  - control-plane/aegisops_control_plane/service.py:935 summary=_⚠️ Potential issue_ | _🟠 Major_ **Avoid leaking sibling recommendation lineage into an anchored recommendation.** Lines 926-935 now pull `alert_id`/`case_id` from every linked... url=https://github.com/TommyKammy/AegisOps/pull/328#discussion_r3055047786
  - control-plane/aegisops_control_plane/service.py:958 summary=_⚠️ Potential issue_ | _🟠 Major_ **Use `AITraceRecord`’s own linkage when building citation context.** By Lines 947-958, `linked_evidence_ids` still only reflects alert/case-de... url=https://github.com/TommyKammy/AegisOps/pull/328#discussion_r3055047787

## Codex Working Notes
### Current Handoff
- Hypothesis: assistant-context snapshots for recommendation and AI-trace records need to surface reviewed alert/case evidence explicitly, not just the local record payload, so advisory output can stay citation-first.
- What changed: tightened `inspect_assistant_context()` so anchored recommendations do not absorb sibling alert/case lineage, and AI-trace snapshots now pull direct evidence from trace subject linkage and material inputs while keeping `linked_evidence_ids` evidence-only.
- Current blocker: none.
- Next exact step: keep watching PR #328 for review/CI; no further local code changes are required for this review slice.
- Verification gap: none for the reviewed slice; the focused persistence module now passes.
- Files touched: `control-plane/tests/test_service_persistence.py`, `control-plane/aegisops_control_plane/service.py`, `.codex-supervisor/issues/322/issue-journal.md`.
- Rollback concern: the assistant-context snapshot now intentionally filters AI-trace material inputs to evidence records only; if a future consumer expects non-evidence IDs in `linked_evidence_ids`, it will need to use a different field.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Turn note: review feedback was validated against the live code and two service regressions were fixed locally.
- Turn note: the focused persistence module passed after the patch set.
- Turn note: the first unittest pass failed because the AI-trace test used an invalid unanchored recommendation fixture and the trace evidence merge still admitted a recommendation ID; both were corrected before the final green run.
