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
Pushed `codex/issue-161` to `origin` and opened draft PR [#169](https://github.com/TommyKammy/AegisOps/pull/169) for the committed documentation and verifier changes. The GitHub app returned `403 Resource not accessible by integration` for PR creation, so PR creation fell back to `gh pr create`, which succeeded.

Focused verification still passes with `bash scripts/verify-control-plane-state-model-doc.sh`.

Summary: Published the branch and opened draft PR #169 after the focused documentation fix for Observation, Lead, and Recommendation.
State hint: pr_open
Blocked reason: none
Tests: `bash scripts/verify-control-plane-state-model-doc.sh`
Next action: Leave PR #169 ready for review or address incoming feedback.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue is a documentation baseline gap, not a runtime/schema gap; the current state-model doc omits Observation, Lead, and Recommendation from the minimum control-plane record family set.
- What changed: Added focused verifier assertions first, reproduced the failure on the old doc, updated the control-plane state-model document to include Observation, Lead, and Recommendation plus distinction notes and reconciliation identifiers, committed the result as `f0a59da`, then published follow-up journal state in `5368b59` and opened draft PR #169.
- Current blocker: none
- Next exact step: Monitor draft PR #169 for review feedback and address any requested changes.
- Verification gap: No broader gap identified; the focused verifier still passes locally after PR publication.
- Files touched: docs/control-plane-state-model.md; scripts/verify-control-plane-state-model-doc.sh; .codex-supervisor/issues/161/issue-journal.md
- Rollback concern: Low; changes are documentation and verifier-only, but the verifier now intentionally enforces the broader minimum-family baseline wording.
- Last focused command: bash scripts/verify-control-plane-state-model-doc.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced failure: `Missing control-plane state model statement: | \`Observation\` | Future AegisOps control-plane observation record | ... |`
- Draft PR: `https://github.com/TommyKammy/AegisOps/pull/169`
- GitHub app PR create failed with `403 Resource not accessible by integration`; `gh pr create --draft` succeeded.
