# Issue #178: validation: harden the control-plane placeholder schema contract

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/178
- Branch: codex/issue-178
- Workspace: .
- Journal: .codex-supervisor/issues/178/issue-journal.md
- Current phase: draft_pr
- Attempt count: 2 (implementation=1, repair=1)
- Last head SHA: b2347f00f04b02ecb4f16c6f4cd59fbafb619aa8
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T14:44:29.968Z

## Latest Codex Summary
Tightened the control-plane placeholder guard so executable live-ish SQL now fails closed while placeholder comments remain allowed. The verifier in [scripts/verify-control-plane-schema-skeleton.sh](scripts/verify-control-plane-schema-skeleton.sh) now rejects runtime-oriented DDL patterns beyond the approved placeholder boundary, and the focused shell coverage in [scripts/test-verify-control-plane-schema-skeleton.sh](scripts/test-verify-control-plane-schema-skeleton.sh) now proves `CREATE TABLE`, `CREATE INDEX`, `ALTER TABLE`/constraint DDL, and seed data fail in the placeholder assets while comment-only mentions still pass.

I also aligned the reviewer-facing contract in [postgres/control-plane/README.md](postgres/control-plane/README.md), [README.md](README.md), and [docs/phase-8-control-plane-foundation-validation.md](docs/phase-8-control-plane-foundation-validation.md), and updated [scripts/verify-phase-8-control-plane-foundation-validation.sh](scripts/verify-phase-8-control-plane-foundation-validation.sh) to enforce that wording. Changes are committed as `68d2e95` and journal follow-up `b2347f0`, pushed to `codex/issue-178`, with draft PR [#192](https://github.com/TommyKammy/AegisOps/pull/192).

Verification ran:
- `bash scripts/verify-control-plane-schema-skeleton.sh`
- `bash scripts/test-verify-control-plane-schema-skeleton.sh`
- `bash scripts/verify-phase-8-control-plane-foundation-validation.sh`
- `rg -n "CREATE TABLE|ALTER TABLE|CREATE INDEX|INSERT" scripts/test-verify-control-plane-schema-skeleton.sh scripts/verify-control-plane-schema-skeleton.sh`

Summary: Hardened the control-plane placeholder schema verifier, added focused fail-closed tests, aligned docs, committed/pushed the branch, and opened draft PR #192.
State hint: draft_pr
Blocked reason: none
Tests: bash scripts/verify-control-plane-schema-skeleton.sh; bash scripts/test-verify-control-plane-schema-skeleton.sh; bash scripts/verify-phase-8-control-plane-foundation-validation.sh; rg -n "CREATE TABLE|ALTER TABLE|CREATE INDEX|INSERT" scripts/test-verify-control-plane-schema-skeleton.sh scripts/verify-control-plane-schema-skeleton.sh
Next action: Await review or follow-up on draft PR #192 and extend verification only if reviewers request broader coverage.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The schema-skeleton verifier only blocked seed `INSERT` statements, so executable control-plane DDL such as `CREATE TABLE`, `ALTER TABLE`, and `CREATE INDEX` could drift into `postgres/control-plane/` without failing validation.
- What changed: Added focused shell-test coverage for allowed placeholder comments plus forbidden live-ish DDL in both placeholder files, added anchored live-DDL rejection to `scripts/verify-control-plane-schema-skeleton.sh`, and aligned reviewer-facing README/Phase 8 validation wording with the fail-closed placeholder boundary.
- Current blocker: none
- Next exact step: Await actionable review on draft PR `#192`; no new review requests or human review comments are present yet.
- Verification gap: None in the requested focused verification set; broader repository verification was not run because the issue guidance was narrowly scoped to the control-plane placeholder contract.
- Files touched: README.md; postgres/control-plane/README.md; docs/phase-8-control-plane-foundation-validation.md; scripts/verify-control-plane-schema-skeleton.sh; scripts/test-verify-control-plane-schema-skeleton.sh; scripts/verify-phase-8-control-plane-foundation-validation.sh
- Rollback concern: The verifier now intentionally rejects additional executable SQL classes in placeholder assets; future approved persistence work will need to update both the verifier and validation docs together rather than dropping DDL into the placeholder skeleton ad hoc.
- Last focused command: gh pr view 192 --json number,title,url,isDraft,reviewRequests,reviews,comments
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
