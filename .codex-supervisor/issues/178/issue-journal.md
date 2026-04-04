# Issue #178: validation: harden the control-plane placeholder schema contract

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/178
- Branch: codex/issue-178
- Workspace: .
- Journal: .codex-supervisor/issues/178/issue-journal.md
- Current phase: draft_pr
- Attempt count: 8 (implementation=1, repair=7)
- Last head SHA: e3fe1caf1d1f1f9bf8a5e54e302af55355951771
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T15:04:55.609Z

## Latest Codex Summary
No code changes were needed. I checked draft PR [#192](https://github.com/TommyKammy/AegisOps/pull/192), confirmed there were no overnight review changes, `verify` is still green, and there are still no human review comments or review requests. I then refreshed the issue journal handoff and pushed that update as `e3fe1ca`.

Summary: Confirmed PR #192 is still green with no overnight review activity, then refreshed and pushed the journal handoff as `e3fe1ca`.
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
- Next exact step: Await actionable review on draft PR `#192`; CI `verify` reran green again and there are still no human review comments or review requests.
- Verification gap: None in the requested focused verification set; broader repository verification was not run because the issue guidance was narrowly scoped to the control-plane placeholder contract.
- Files touched: README.md; postgres/control-plane/README.md; docs/phase-8-control-plane-foundation-validation.md; scripts/verify-control-plane-schema-skeleton.sh; scripts/test-verify-control-plane-schema-skeleton.sh; scripts/verify-phase-8-control-plane-foundation-validation.sh
- Rollback concern: The verifier now intentionally rejects additional executable SQL classes in placeholder assets; future approved persistence work will need to update both the verifier and validation docs together rather than dropping DDL into the placeholder skeleton ad hoc.
- Last focused command: gh pr view 192 --json number,title,url,isDraft,reviewRequests,reviews,comments,statusCheckRollup
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
