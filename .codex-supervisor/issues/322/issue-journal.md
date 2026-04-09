# Issue #322: implementation: deliver advisory-only AI triage summaries and recommendation drafts with citations to reviewed records and evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/322
- Branch: codex/issue-322
- Workspace: .
- Journal: .codex-supervisor/issues/322/issue-journal.md
- Current phase: addressing_review
- Attempt count: 7 (implementation=2, repair=3)
- Last head SHA: b990857bca14dcf3ce98120e75d36301b1f7ef58
- Blocked reason: manual_review
- Last failure signature: PRRT_kwDOR2iDUc55uaMq|PRRT_kwDOR2iDUc55uaMt
- Repeated failure signature count: 1
- Updated at: 2026-04-09T02:06:16Z

## Latest Codex Summary
Fixed the unresolved review feedback in `control-plane/aegisops_control_plane/service.py` by backfilling evidence-derived alert/case anchors before materializing the alert/case payloads, and tightened the AI-trace evidence assertions in `control-plane/tests/test_service_persistence.py` to exact membership checks. Committed as `b990857`.

Summary: Addressed the remaining review feedback with a focused service fix and a stricter persistence assertion, then pushed the branch.
State hint: addressing_review
Blocked reason: manual_review
Tests: `python3 -m unittest control-plane.tests.test_service_persistence`
Next action: manually resolve or re-review the remaining GitHub review threads on PR #328.
Failure signature: PRRT_kwDOR2iDUc55uaMq|PRRT_kwDOR2iDUc55uaMt

## Active Failure Context
- Category: review
- Summary: 2 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/328#discussion_r3055111263
- Details:
  - control-plane/aegisops_control_plane/service.py:978 summary=_⚠️ Potential issue_ | _🟠 Major_ **Fold evidence-derived anchors back in before building alert/case payloads.** `linked_alert_records` / `linked_case_records` are materialized ... url=https://github.com/TommyKammy/AegisOps/pull/328#discussion_r3055111263
  - control-plane/tests/test_service_persistence.py:500 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Tighten evidence assertions to prevent false positives in leakage scenarios.** `assertIn` + `len >= 1` can still pass when unrelated evidence... url=https://github.com/TommyKammy/AegisOps/pull/328#discussion_r3055111267

## Codex Working Notes
### Current Handoff
- Hypothesis: assistant-context snapshots for recommendation and AI-trace records need to surface reviewed alert/case evidence explicitly, not just the local record payload, while avoiding sibling-lineage bleed-through from anchored recommendations.
- What changed: backfilled evidence-derived alert/case anchors before materializing assistant context payloads, tightened the AI-trace citation test to exact evidence membership, and pushed the branch.
- Current blocker: manual review closeout on GitHub.
- Next exact step: resolve or re-review the remaining PR threads now that the code is updated and verified.
- Verification gap: none for the reviewed slice; the focused persistence module passes.
- Files touched: `control-plane/tests/test_service_persistence.py`, `control-plane/aegisops_control_plane/service.py`, `.codex-supervisor/issues/322/issue-journal.md`.
- Rollback concern: evidence-derived alert/case anchors now feed assistant context snapshots before payload materialization; if a future consumer depends on the pre-backfill order, it will need a narrower helper.
- Last focused command: `gh api graphql -f query='query($owner:String!, $name:String!, $number:Int!){ repository(owner:$owner,name:$name){ pullRequest(number:$number){ reviewThreads(first:100){ nodes { id isResolved isOutdated path line originalLine comments(first:5){ nodes { id body author { login } } } } } } } }' -F owner=TommyKammy -F name=AegisOps -F number=328`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Turn note: review feedback was validated against the live code and fixed locally with one service change and one test hardening.
- Turn note: the focused persistence module passed after the patch set.
