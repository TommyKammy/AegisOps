# Issue #147: design: define the safe query gateway and tool policy for AI-assisted hunt workflows

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/147
- Branch: codex/issue-147
- Workspace: .
- Journal: .codex-supervisor/issues/147/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 4c5ebbf0a65a9a158b333333d96cffe1e5230844
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T00:47:27.262Z

## Latest Codex Summary
- Added a focused Safe Query Gateway doc verifier and fixture-backed test, reproduced the workspace failure as a missing `docs/safe-query-gateway-and-tool-policy.md`, then added the design document and passed focused verification.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue `#147` was failing because the repository had no dedicated Safe Query Gateway design or verifier encoding the bounded AI-hunt read contract.
- What changed: Added `scripts/verify-safe-query-gateway-doc.sh`, added `scripts/test-verify-safe-query-gateway-doc.sh`, and authored `docs/safe-query-gateway-and-tool-policy.md` covering structured query intent, deterministic query generation, allowlists, caps, citations, trust classes, and failure handling.
- Current blocker: none
- Next exact step: Stage the new doc and verifier files, create a checkpoint commit on `codex/issue-147`, and keep the branch ready for PR creation or follow-up review.
- Verification gap: No broader CI run yet; focused doc verification only.
- Files touched: `docs/safe-query-gateway-and-tool-policy.md`, `scripts/verify-safe-query-gateway-doc.sh`, `scripts/test-verify-safe-query-gateway-doc.sh`
- Rollback concern: Low; changes are additive documentation and doc-verification scripts only.
- Last focused command: `bash scripts/verify-safe-query-gateway-doc.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced missing-doc failure before implementation: `Missing safe query gateway document: /Users/jp.infra/Dev/AegisOps-worktrees/issue-147/docs/safe-query-gateway-and-tool-policy.md`
- Focused checks run: `bash scripts/test-verify-safe-query-gateway-doc.sh`, `bash scripts/verify-safe-query-gateway-doc.sh`, `rg -n "Safe Query Gateway|query intent|citation|allowlist|time cap|row cap|aggregation|cost budget|trust boundary" docs`, `bash scripts/verify-response-action-safety-model-doc.sh`, `bash scripts/verify-auth-baseline-doc.sh`
