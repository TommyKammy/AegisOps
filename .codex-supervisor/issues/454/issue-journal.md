# Issue #454: cleanup: remove duplicated low-level validators and normalize shared helper placement in service.py

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/454
- Branch: codex/issue-454
- Workspace: .
- Journal: .codex-supervisor/issues/454/issue-journal.md
- Current phase: addressing_review
- Attempt count: 4 (implementation=1, repair=3)
- Last head SHA: 98b53cf13283b8ddc008da585d0357407c782f77
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc56rYGh|PRRT_kwDOR2iDUc56rdC5
- Repeated failure signature count: 1
- Updated at: 2026-04-14T00:09:40.3NZ

## Latest Codex Summary
Checked PR #464 review-thread state with `gh pr view` plus the `gh-address-comments` thread fetcher and confirmed the service normalization comment is already resolved on head `98b53cf`; the remaining actionable work was the stale journal snapshot plus missing Ruff suppressions on the trusted-proxy Wazuh ingest tests in [test_cli_inspection.py](control-plane/tests/test_cli_inspection.py:1411).

I added `# noqa` suppressions for intentional `S104` and `S106` fixtures across the three contiguous trusted-proxy Wazuh ingest tests, re-ran the requested unittest suites successfully, and refreshed this journal against the latest verification pass. Local lint verification was limited because `ruff` is not installed in this workspace.

Summary: Added Ruff suppressions for the intentional non-loopback/secret proxy-ingest test fixtures, re-ran the requested unittest suites, and refreshed the issue journal against the current PR review state.
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection control-plane.tests.test_phase21_runtime_auth_validation`
Next action: Commit and push the Ruff-suppression/journal refresh so PR #464 can re-evaluate the remaining review threads.
Failure signature: PRRT_kwDOR2iDUc56rYGh|PRRT_kwDOR2iDUc56rdC5

## Active Failure Context
- Category: review
- Summary: 2 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/464#discussion_r3076426214
- Details:
  - .codex-supervisor/issues/454/issue-journal.md:15 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Sync snapshot metadata with the latest PR state.** `Current phase`, `Last head SHA`, and timestamp appear stale versus this PR context (e.g.,... url=https://github.com/TommyKammy/AegisOps/pull/464#discussion_r3076426214
  - control-plane/tests/test_cli_inspection.py:1467 summary=_⚠️ Potential issue_ | _🟠 Major_ **Add Ruff security suppressions to keep this test consistent and CI-clean.** This new test introduces S104/S106 violations (bind-all-interface... url=https://github.com/TommyKammy/AegisOps/pull/464#discussion_r3076453666

## Codex Working Notes
### Current Handoff
- Hypothesis: Publishing the new test-fixture suppression patch and this journal refresh should address both remaining automated review threads on PR #464.
- What changed: Added inline `# noqa: S104` / `# noqa: S106` suppressions to the three contiguous trusted-proxy Wazuh ingest tests in `control-plane/tests/test_cli_inspection.py` and refreshed the journal after re-checking the live PR thread state.
- Current blocker: none
- Next exact step: Commit and push `codex/issue-454`, then re-check the unresolved review-thread state on PR #464.
- Verification gap: No local Ruff binary is available in this workspace, so lint confirmation is by targeted file inspection plus the existing review finding; the requested unittest suites passed after the edit.
- Files touched: `control-plane/tests/test_cli_inspection.py`, `.codex-supervisor/issues/454/issue-journal.md`
- Rollback concern: Low; the code change is comment-only in tests and does not alter runtime behavior.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection control-plane.tests.test_phase21_runtime_auth_validation`
### Scratchpad
- `gh pr view 464` and `fetch_comments.py --repo TommyKammy/AegisOps --pr 464` showed PR head `98b53cf13283b8ddc008da585d0357407c782f77`, one resolved service thread, and two unresolved threads for the journal snapshot plus CLI-inspection fixture suppressions.
