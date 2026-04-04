# Issue #178: validation: harden the control-plane placeholder schema contract

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/178
- Branch: codex/issue-178
- Workspace: .
- Journal: .codex-supervisor/issues/178/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 4fedb25a5ba5442eec38cb6510d10a265938153e
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T14:36:48.972Z

## Latest Codex Summary
- Reproduced that `scripts/verify-control-plane-schema-skeleton.sh` allowed executable `CREATE TABLE` statements in placeholder assets, then tightened the focused shell tests and verifier so placeholder comments remain allowed while live-ish DDL now fails closed in `schema.sql` and the migration skeleton. Aligned `README.md`, `postgres/control-plane/README.md`, and `docs/phase-8-control-plane-foundation-validation.md` with the stricter placeholder-only contract and reran the focused verification set successfully.
- Committed the guard tightening as `68d2e95` (`Harden control-plane placeholder schema guard`), pushed `codex/issue-178`, and opened draft PR `#192` for review continuity.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The schema-skeleton verifier only blocked seed `INSERT` statements, so executable control-plane DDL such as `CREATE TABLE`, `ALTER TABLE`, and `CREATE INDEX` could drift into `postgres/control-plane/` without failing validation.
- What changed: Added focused shell-test coverage for allowed placeholder comments plus forbidden live-ish DDL in both placeholder files, added anchored live-DDL rejection to `scripts/verify-control-plane-schema-skeleton.sh`, and aligned reviewer-facing README/Phase 8 validation wording with the fail-closed placeholder boundary.
- Current blocker: none
- Next exact step: Await review on draft PR `#192` or continue with any requested follow-up verification/edits.
- Verification gap: None in the requested focused verification set; broader repository verification was not run because the issue guidance was narrowly scoped to the control-plane placeholder contract.
- Files touched: README.md; postgres/control-plane/README.md; docs/phase-8-control-plane-foundation-validation.md; scripts/verify-control-plane-schema-skeleton.sh; scripts/test-verify-control-plane-schema-skeleton.sh; scripts/verify-phase-8-control-plane-foundation-validation.sh
- Rollback concern: The verifier now intentionally rejects additional executable SQL classes in placeholder assets; future approved persistence work will need to update both the verifier and validation docs together rather than dropping DDL into the placeholder skeleton ad hoc.
- Last focused command: gh pr view 192 --json body,url
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
