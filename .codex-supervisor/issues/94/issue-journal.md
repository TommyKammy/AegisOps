# Issue #94: design: define AegisOps authN, authZ, and service account ownership baseline

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/94
- Branch: codex/issue-94
- Workspace: .
- Journal: .codex-supervisor/issues/94/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: dcd40bd75842d33d3c118e6b8a803fc79b67d4b7
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-02T18:19:42.102Z

## Latest Codex Summary
- Added a dedicated auth baseline artifact at `docs/auth-baseline.md` plus a focused verifier/test pair to make the missing baseline reproducible and then enforce the required persona, least-privilege, service-account, and secret-lifecycle statements.
- Updated baseline references in `README.md`, `docs/documentation-ownership-map.md`, and `scripts/verify-documentation-ownership-map.sh`.
- Reproduced the initial failure as `Missing auth baseline document: /Users/jp.infra/Dev/AegisOps-worktrees/issue-94/docs/auth-baseline.md`, then cleared it with focused verification.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was a missing policy artifact rather than a runtime defect, so the narrowest reproducible failure was an explicit verifier for a missing auth baseline document.
- What changed: Added `docs/auth-baseline.md`; added `scripts/verify-auth-baseline-doc.sh` and `scripts/test-verify-auth-baseline-doc.sh`; updated README and documentation ownership references; updated the ownership-map verifier to require the new doc entry.
- Current blocker: none
- Next exact step: Stage the touched files, create a checkpoint commit for the auth baseline slice, and keep the branch ready for draft PR creation or follow-on review.
- Verification gap: README listing is not covered by a dedicated verifier, but the new auth verifier, its fixture test, and the touched ownership-map verifier all pass.
- Files touched: `docs/auth-baseline.md`, `scripts/verify-auth-baseline-doc.sh`, `scripts/test-verify-auth-baseline-doc.sh`, `README.md`, `docs/documentation-ownership-map.md`, `scripts/verify-documentation-ownership-map.sh`, `.codex-supervisor/issues/94/issue-journal.md`
- Rollback concern: Low; changes are documentation and verifier-only, but future edits should keep the auth baseline wording aligned with the verifier's exact required phrases.
- Last focused command: `bash scripts/verify-auth-baseline-doc.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
