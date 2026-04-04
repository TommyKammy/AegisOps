# Issue #178: validation: harden the control-plane placeholder schema contract

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/178
- Branch: codex/issue-178
- Workspace: .
- Journal: .codex-supervisor/issues/178/issue-journal.md
- Current phase: draft_pr
- Attempt count: 3 (implementation=1, repair=2)
- Last head SHA: cab652de5d5279bbba63d051c2e3db15964229da
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T14:48:02.170Z

## Latest Codex Summary
No code changes were needed. I checked draft PR [#192](https://github.com/TommyKammy/AegisOps/pull/192), confirmed there are still no actionable human reviews or review requests, updated the issue journal handoff to reflect that waiting state, and pushed the journal refresh as `cab652d`.

I did not run additional verification this turn because the branch content did not change beyond the journal update and there was no new review-driven work to validate.

Summary: Checked draft PR #192, found no actionable review feedback, refreshed the issue journal handoff, and pushed commit `cab652d`.
State hint: draft_pr
Blocked reason: none
Tests: not run this turn; checked PR status with `gh pr view 192 --json number,title,url,isDraft,reviewRequests,reviews,comments`
Next action: Await actionable review or follow-up instructions on draft PR #192.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The schema-skeleton verifier only blocked seed `INSERT` statements, so executable control-plane DDL such as `CREATE TABLE`, `ALTER TABLE`, and `CREATE INDEX` could drift into `postgres/control-plane/` without failing validation.
- What changed: Added focused shell-test coverage for allowed placeholder comments plus forbidden live-ish DDL in both placeholder files, added anchored live-DDL rejection to `scripts/verify-control-plane-schema-skeleton.sh`, and aligned reviewer-facing README/Phase 8 validation wording with the fail-closed placeholder boundary.
- Current blocker: none
- Next exact step: Await actionable review on draft PR `#192`; CI `verify` is green and there are still no human review comments or review requests.
- Verification gap: None in the requested focused verification set; broader repository verification was not run because the issue guidance was narrowly scoped to the control-plane placeholder contract.
- Files touched: README.md; postgres/control-plane/README.md; docs/phase-8-control-plane-foundation-validation.md; scripts/verify-control-plane-schema-skeleton.sh; scripts/test-verify-control-plane-schema-skeleton.sh; scripts/verify-phase-8-control-plane-foundation-validation.sh
- Rollback concern: The verifier now intentionally rejects additional executable SQL classes in placeholder assets; future approved persistence work will need to update both the verifier and validation docs together rather than dropping DDL into the placeholder skeleton ad hoc.
- Last focused command: gh pr view 192 --json number,title,url,isDraft,reviewRequests,reviews,comments,statusCheckRollup
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
