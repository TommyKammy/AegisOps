# Issue #161: design: extend the control-plane minimum record family for observation, lead, and recommendation

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/161
- Branch: codex/issue-161
- Workspace: .
- Journal: .codex-supervisor/issues/161/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: b40ec16b6619c17f6ecc0de7751edb0361ba87fb
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T07:06:37.448Z

## Latest Codex Summary
- Tightened the control-plane state-model verifier to require Observation, Lead, and Recommendation as minimum control-plane record families with explicit distinction language against Evidence, AI Trace, Alert, and Case state.
- Reproduced the gap with `bash scripts/verify-control-plane-state-model-doc.sh`, which failed on the missing `Observation` statement before the document update.
- Updated `docs/control-plane-state-model.md` to add the three record families, extend the minimum-family baseline, and preserve narrow runtime scope.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue is a documentation baseline gap, not a runtime/schema gap; the current state-model doc omits Observation, Lead, and Recommendation from the minimum control-plane record family set.
- What changed: Added focused verifier assertions first, reproduced the failure on the old doc, then updated the control-plane state-model document to include Observation, Lead, and Recommendation plus distinction notes and reconciliation identifiers.
- Current blocker: none
- Next exact step: Commit the focused doc and verifier changes, then leave the branch ready for draft PR or review.
- Verification gap: No broader gap identified; focused grep and verifier both pass locally.
- Files touched: docs/control-plane-state-model.md; scripts/verify-control-plane-state-model-doc.sh; .codex-supervisor/issues/161/issue-journal.md
- Rollback concern: Low; changes are documentation and verifier-only, but the verifier now intentionally enforces the broader minimum-family baseline wording.
- Last focused command: bash scripts/verify-control-plane-state-model-doc.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced failure: `Missing control-plane state model statement: | \`Observation\` | Future AegisOps control-plane observation record | ... |`
