# Issue #147: design: define the safe query gateway and tool policy for AI-assisted hunt workflows

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/147
- Branch: codex/issue-147
- Workspace: .
- Journal: .codex-supervisor/issues/147/issue-journal.md
- Current phase: draft_pr
- Attempt count: 8 (implementation=3, repair=5)
- Last head SHA: 54b5d02a992e8ca5818fb99bbd33920d54418d70
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T01:17:23.464Z

## Latest Codex Summary
Draft PR `#155` is still unchanged: `OPEN`, `isDraft=true`, `mergeStateStatus=CLEAN`, no review submissions, and no actionable feedback beyond the existing CodeRabbit draft-skipped status comment. This turn was another monitoring pass only, so I kept the branch scoped to a journal refresh and avoided implementation churn.

Summary: Rechecked draft PR `#155`, confirmed it is still waiting on real review feedback, and refreshed the journal handoff.
State hint: draft_pr
Blocked reason: none
Tests: Not run in this turn; PR state only was checked with `gh pr view 155 --json url,number,state,isDraft,reviewDecision,mergeStateStatus,comments,reviews`
Next action: Monitor draft PR `#155` for review feedback or reviewer-requested CI before making further changes
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue `#147` was failing because the repository had no dedicated Safe Query Gateway design or verifier encoding the bounded AI-hunt read contract.
- What changed: Added `scripts/verify-safe-query-gateway-doc.sh`, added `scripts/test-verify-safe-query-gateway-doc.sh`, and authored `docs/safe-query-gateway-and-tool-policy.md` covering structured query intent, deterministic query generation, allowlists, caps, citations, trust classes, and failure handling.
- Current blocker: none
- Next exact step: Monitor draft PR `#155` and address real review feedback if it arrives, or run broader repo CI only if a reviewer asks for more than the focused documentation checks.
- Verification gap: Broader repo CI has still not been run; the last focused issue verification set remains the latest substantive validation.
- Files touched: `docs/safe-query-gateway-and-tool-policy.md`, `scripts/verify-safe-query-gateway-doc.sh`, `scripts/test-verify-safe-query-gateway-doc.sh`
- Rollback concern: Low; changes are additive documentation and doc-verification scripts only.
- Last focused command: `gh pr view 155 --json url,number,state,isDraft,reviewDecision,mergeStateStatus,comments,reviews`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced missing-doc failure before implementation: `Missing safe query gateway document: docs/safe-query-gateway-and-tool-policy.md`
- Focused checks run: `bash scripts/test-verify-safe-query-gateway-doc.sh`, `bash scripts/verify-safe-query-gateway-doc.sh`, `rg -n "Safe Query Gateway|query intent|citation|allowlist|time cap|row cap|aggregation|cost budget|trust boundary" docs`, `bash scripts/verify-response-action-safety-model-doc.sh`, `bash scripts/verify-auth-baseline-doc.sh`
- Safe-query checks rerun during stabilizing: `bash scripts/test-verify-safe-query-gateway-doc.sh`, `bash scripts/verify-safe-query-gateway-doc.sh`
- Draft PR opened: `https://github.com/TommyKammy/AegisOps/pull/155`
- PR creation fallback used because connector create failed with `403 Resource not accessible by integration`
- Current PR state check: `gh pr view 155 --json url,number,state,isDraft,reviewDecision,mergeStateStatus,comments,reviews` reported `state=OPEN`, `isDraft=true`, `mergeStateStatus=CLEAN`, and no review submissions
- Latest PR state recheck in this turn remained unchanged except for the CodeRabbit run identifier in the draft-skipped status comment
- Latest monitoring pass again found no new reviews, no merge-state change, and no reviewer-requested CI
- Current monitoring pass again found no new reviews, no merge-state change, and no reviewer-requested CI
- Latest monitoring pass also found no new reviews, no merge-state change, and no reviewer-requested CI
