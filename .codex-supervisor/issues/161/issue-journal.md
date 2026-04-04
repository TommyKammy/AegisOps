# Issue #161: design: extend the control-plane minimum record family for observation, lead, and recommendation

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/161
- Branch: codex/issue-161
- Workspace: .
- Journal: .codex-supervisor/issues/161/issue-journal.md
- Current phase: repairing_ci
- Attempt count: 4 (implementation=3, repair=1)
- Last head SHA: 92873a01080a5975e48034251c0570856c514c4f
- Blocked reason: none
- Last failure signature: verify:fail
- Repeated failure signature count: 1
- Updated at: 2026-04-04T07:18:25.263Z

## Latest Codex Summary
Published `codex/issue-161`, opened draft PR [#169](https://github.com/TommyKammy/AegisOps/pull/169), and updated the durable handoff in [issue-journal.md](.codex-supervisor/issues/161/issue-journal.md) to reflect the PR state. The GitHub app could not create the PR because of a `403 Resource not accessible by integration`, so I used `gh pr create --draft` as the fallback.

The focused verifier still passes, and the branch is clean aside from untracked supervisor session artifacts. Latest pushed commit: `92873a0`.

Summary: Pushed the branch, opened draft PR #169, updated the issue journal handoff, and reconfirmed the focused doc verifier.
State hint: pr_open
Blocked reason: none
Tests: `bash scripts/verify-control-plane-state-model-doc.sh`
Next action: Monitor draft PR #169 for review feedback and address any requested changes.
Failure signature: verify:fail

## Active Failure Context
- Category: checks
- Summary: PR #169 has failing checks.
- Command or source: gh pr checks
- Reference: https://github.com/TommyKammy/AegisOps/pull/169
- Details:
  - verify (fail/FAILURE) https://github.com/TommyKammy/AegisOps/actions/runs/23974006640/job/69928100977

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining CI failure is a stale focused test fixture, not a document or verifier defect; `scripts/test-verify-control-plane-state-model-doc.sh` still models the pre-Observation/Lead/Recommendation baseline.
- What changed: Reproduced the failing `verify` check locally, confirmed the same failure from GitHub Actions logs, and updated the focused test fixture so its synthetic valid document now includes Observation, Lead, Recommendation, the expanded minimum-family statement, and the added distinction/reconciliation notes.
- Current blocker: none
- Next exact step: Commit the focused test repair, push `codex/issue-161`, and watch PR #169 for a fresh `verify` result.
- Verification gap: The targeted verifier and paired shell test now pass locally; the refreshed GitHub Actions run is still pending because the repair has not been pushed yet.
- Files touched: docs/control-plane-state-model.md; scripts/verify-control-plane-state-model-doc.sh; scripts/test-verify-control-plane-state-model-doc.sh; .codex-supervisor/issues/161/issue-journal.md
- Rollback concern: Low; the repair only aligns the focused shell test fixture with the already-approved document and verifier wording.
- Last focused command: bash scripts/test-verify-control-plane-state-model-doc.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced failure: `Expected verifier to pass for .../valid` followed by `Missing control-plane state model statement: | \`Observation\` | Future AegisOps control-plane observation record | ... |`
- Actions log match: `gh run view 23974006640 --log-failed` shows the same failure inside `bash scripts/test-verify-control-plane-state-model-doc.sh`
- Commands run this turn: `gh auth status`; `gh pr checks 169`; `gh run view 23974006640 --log-failed`; `bash scripts/verify-control-plane-state-model-doc.sh`; `bash scripts/test-verify-control-plane-state-model-doc.sh`
- Draft PR: `https://github.com/TommyKammy/AegisOps/pull/169`
- GitHub app PR create failed with `403 Resource not accessible by integration`; `gh pr create --draft` succeeded.
