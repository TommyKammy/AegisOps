# Issue #178: validation: harden the control-plane placeholder schema contract

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/178
- Branch: codex/issue-178
- Workspace: .
- Journal: .codex-supervisor/issues/178/issue-journal.md
- Current phase: draft_pr
- Attempt count: 75 (implementation=1, repair=14)
- Last head SHA: 1886d569e0eaba31c996e160240c50d4ab9b0a21
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T18:59:41.119Z

## Latest Codex Summary
No code changes were needed. I checked draft PR [#192](https://github.com/TommyKammy/AegisOps/pull/192), confirmed it is still a draft with no human review comments or review requests, and that `verify` remains green. I then refreshed the issue journal handoff for the current durable state.

Summary: Confirmed PR #192 is still green and waiting on review, then refreshed the journal handoff for the current durable state.
State hint: draft_pr
Blocked reason: none
Tests: not run this turn; checked PR state with `gh pr view 192 --json number,title,url,isDraft,reviewRequests,reviews,comments,statusCheckRollup`
Next action: Await actionable review on draft PR #192.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The schema-skeleton verifier only blocked seed `INSERT` statements, so executable control-plane DDL such as `CREATE TABLE`, `ALTER TABLE`, and `CREATE INDEX` could drift into `postgres/control-plane/` without failing validation.
- What changed: Added focused shell-test coverage for allowed placeholder comments plus forbidden live-ish DDL in both placeholder files, added anchored live-DDL rejection to `scripts/verify-control-plane-schema-skeleton.sh`, and aligned reviewer-facing README/Phase 8 validation wording with the fail-closed placeholder boundary.
- Current blocker: none
- Next exact step: Await actionable review on draft PR `#192`; the draft PR remains green after the latest status check, `verify` last completed successfully at 2026-04-04T18:57:11Z, and there are still no human review comments or review requests.
- Verification gap: None in the requested focused verification set; broader repository verification was not run because the issue guidance was narrowly scoped to the control-plane placeholder contract.
- Files touched: README.md; postgres/control-plane/README.md; docs/phase-8-control-plane-foundation-validation.md; scripts/verify-control-plane-schema-skeleton.sh; scripts/test-verify-control-plane-schema-skeleton.sh; scripts/verify-phase-8-control-plane-foundation-validation.sh
- Rollback concern: The verifier now intentionally rejects additional executable SQL classes in placeholder assets; future approved persistence work will need to update both the verifier and validation docs together rather than dropping DDL into the placeholder skeleton ad hoc.
- Last focused command: gh pr view 192 --json number,title,url,isDraft,reviewRequests,reviews,comments,statusCheckRollup
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
