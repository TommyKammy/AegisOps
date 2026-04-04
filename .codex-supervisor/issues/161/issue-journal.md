# Issue #161: design: extend the control-plane minimum record family for observation, lead, and recommendation

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/161
- Branch: codex/issue-161
- Workspace: .
- Journal: .codex-supervisor/issues/161/issue-journal.md
- Current phase: stabilizing
- Attempt count: 3 (implementation=3, repair=0)
- Last head SHA: f0a59dae12f069a1765d1401eb2c488bd81c67ce
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T07:14:18.650Z

## Latest Codex Summary
Updated the handoff in [issue-journal.md](.codex-supervisor/issues/161/issue-journal.md) so it reflects the actual durable state: the scoped doc/verifier work is already committed as `f0a59da`, the branch is ahead by one commit, and the next step is draft PR or review. No code or doc content changed beyond the journal handoff.

Focused verification still passes with `bash scripts/verify-control-plane-state-model-doc.sh`.

Summary: Refreshed the issue journal handoff to match the committed stabilization state and rechecked the focused verifier.
State hint: draft_pr
Blocked reason: none
Tests: `bash scripts/verify-control-plane-state-model-doc.sh`
Next action: Open a draft PR for `codex/issue-161` or hand the committed checkpoint to review.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue is a documentation baseline gap, not a runtime/schema gap; the current state-model doc omits Observation, Lead, and Recommendation from the minimum control-plane record family set.
- What changed: Added focused verifier assertions first, reproduced the failure on the old doc, updated the control-plane state-model document to include Observation, Lead, and Recommendation plus distinction notes and reconciliation identifiers, and committed the result as `f0a59da`.
- Current blocker: none
- Next exact step: Open a draft PR for `codex/issue-161` or hand the committed checkpoint to review.
- Verification gap: No broader gap identified; the focused verifier still passes locally in stabilizing state.
- Files touched: docs/control-plane-state-model.md; scripts/verify-control-plane-state-model-doc.sh; .codex-supervisor/issues/161/issue-journal.md
- Rollback concern: Low; changes are documentation and verifier-only, but the verifier now intentionally enforces the broader minimum-family baseline wording.
- Last focused command: bash scripts/verify-control-plane-state-model-doc.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced failure: `Missing control-plane state model statement: | \`Observation\` | Future AegisOps control-plane observation record | ... |`
- Branch status: `codex/issue-161` is ahead of `origin/main` by 1 commit and ready for draft PR/review; remaining untracked `.codex-supervisor` files are session artifacts.
