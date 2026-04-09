# Issue #322: implementation: deliver advisory-only AI triage summaries and recommendation drafts with citations to reviewed records and evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/322
- Branch: codex/issue-322
- Workspace: .
- Journal: .codex-supervisor/issues/322/issue-journal.md
- Current phase: addressing_review
- Attempt count: 4 (implementation=2, repair=2)
- Last head SHA: ea33539e825f67346e1d683d1ad4288c8d29d43f
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc55uOxH
- Repeated failure signature count: 1
- Updated at: 2026-04-09T01:48:01.839Z

## Latest Codex Summary
Summary: Validated the advisory-only citation fixes in commit `ea33539`; the remaining PR thread is the stale journal phase-label comment, which no longer matches the current `addressing_review` state.
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence`
Next action: commit and push the journal refresh so PR #328 reflects the current phase label, then let review/CI settle the outdated journal thread
Failure signature: discussion_r3055047785

## Active Failure Context
- Category: review
- Summary: 1 unresolved automated review thread remains, but it is an outdated comment on the issue journal rather than a code regression.
- Reference: https://github.com/TommyKammy/AegisOps/pull/328#discussion_r3055047785
- Details:
  - .codex-supervisor/issues/322/issue-journal.md:8 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Clarify the current phase status.** The current journal now says `Current phase: addressing_review`, so the earlier `reproducing` label is stale and the thread is outdated.

## Codex Working Notes
### Current Handoff
- Hypothesis: assistant-context snapshots for recommendation and AI-trace records need to surface reviewed alert/case evidence explicitly, not just the local record payload, while avoiding sibling-lineage bleed-through from anchored recommendations.
- What changed: tightened `inspect_assistant_context()` so anchored recommendations do not absorb sibling alert/case lineage, and AI-trace snapshots now pull direct evidence from trace subject linkage and material inputs while keeping `linked_evidence_ids` evidence-only; the live PR review threads on `service.py` are resolved.
- Current blocker: none.
- Next exact step: commit and push the journal refresh so the issue record matches the live PR thread state.
- Verification gap: none for the reviewed slice; the focused persistence module now passes.
- Files touched: `control-plane/tests/test_service_persistence.py`, `control-plane/aegisops_control_plane/service.py`, `.codex-supervisor/issues/322/issue-journal.md`.
- Rollback concern: the assistant-context snapshot now intentionally filters AI-trace material inputs to evidence records only; if a future consumer expects non-evidence IDs in `linked_evidence_ids`, it will need to use a different field.
- Last focused command: `gh api graphql -f query='query($owner:String!, $name:String!, $number:Int!){ repository(owner:$owner,name:$name){ pullRequest(number:$number){ reviewThreads(first:100){ nodes { isResolved isOutdated path line originalLine comments(first:20){ nodes { body author { login } path line originalLine createdAt } } } } } } }' -F owner=TommyKammy -F name=AegisOps -F number=328`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Turn note: review feedback was validated against the live code and two service regressions were fixed locally.
- Turn note: the focused persistence module passed after the patch set.
- Turn note: the first unittest pass failed because the AI-trace test used an invalid unanchored recommendation fixture and the trace evidence merge still admitted a recommendation ID; both were corrected before the final green run.
