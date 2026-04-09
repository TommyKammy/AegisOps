# Issue #322: implementation: deliver advisory-only AI triage summaries and recommendation drafts with citations to reviewed records and evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/322
- Branch: codex/issue-322
- Workspace: .
- Journal: .codex-supervisor/issues/322/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 7 (implementation=2, repair=2)
- Last head SHA: 9f8be26def84f6cba2babe378fcc34413bcd6e2d
- Blocked reason: none
- Last failure signature: local-review:high:high:3:1:clean
- Repeated failure signature count: 2
- Updated at: 2026-04-09T02:37:03.284Z

## Latest Codex Summary
The live service code already had the late recommendation-lineage ordering in place, so I hardened the evidence-only AI-trace regression test to assert the reviewed context plus linked alert/case records that the review was concerned about. I also fixed the test fixture to define the reviewed-context payload explicitly. Verified with the focused persistence suite.

Summary: Hardened evidence-only AI-trace citation coverage with reviewed-context assertions
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence`
Next action: request a fresh review pass on PR #328 after commit
Failure signature: local-review:high:high:3:1:clean

## Active Failure Context
- Category: blocked
- Summary: Local review found 3 actionable finding(s) across 3 root cause(s); max severity=high; verified high-severity findings=1; verified max severity=high.
- Details:
  - findings=3
  - root_causes=3
  - summary=<redacted-local-path>

## Codex Working Notes
### Current Handoff
- Hypothesis: the citation-ready AI-trace path is already correct in service code, but the evidence-only regression needed explicit assertions for `reviewed_context` and the linked alert/case records.
- What changed: hardened `test_service_includes_evidence_derived_recommendations_in_ai_trace_context` to assert reviewed context plus alert/case citation records, and fixed the test fixture to define that reviewed context locally.
- Current blocker: none locally; the focused persistence module passes.
- Next exact step: commit the test hardening, then request a fresh review pass on PR #328.
- Verification gap: none for the reviewed slice; the focused persistence module passes.
- Files touched: `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/322/issue-journal.md`.
- Rollback concern: the new assertions depend on the evidence-only AI-trace citation path still surfacing alert/case anchors through recommendation lineage.
- Last focused commands: `python3 -m unittest control-plane.tests.test_service_persistence`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Turn note: the live service code already reflected the ordering fix; the remaining work was to pin the citation-ready behavior with assertions.
- Turn note: the focused persistence module passed after the test hardening.
