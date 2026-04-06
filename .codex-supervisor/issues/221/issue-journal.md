# Issue #221: validation: make the Phase 10 thesis verifiers reject stale README and pre-runtime control-plane wording

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/221
- Branch: codex/issue-221
- Workspace: .
- Journal: .codex-supervisor/issues/221/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: d0e32a4f6a2c24b711cbbbcde72bdef1ff7f33ef
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-06T04:29:52.980Z

## Latest Codex Summary
- Reproduced that the Phase 10 README, control-plane state-model, and top-level thesis verifiers all passed when stale foundation-phase README wording and pre-runtime control-plane wording were appended alongside the new required text.
- Tightened the focused verifier tests first, then updated the README and control-plane verifier forbidden-phrase lists so those stale statements now fail closed and bubble through the top-level Phase 10 verifier.
- Verified the focused test scripts, the three requested verifier scripts, and one explicit negative check that removed a required README thesis marker in a temporary repo copy and confirmed the README verifier failed.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The child verifiers required the new runtime-era wording but did not reject older contradictory README and control-plane state-model lines when those lines reappeared alongside the required text.
- What changed: Added focused failing cases to the three Phase 10 verifier test scripts; extended `scripts/verify-readme-and-repository-structure-control-plane-thesis.sh` to reject stale foundation-phase and OpenSearch/n8n-centric README lines; extended `scripts/verify-control-plane-state-model-doc.sh` to reject pre-runtime "future control layer/control record" wording.
- Current blocker: none
- Next exact step: Review diff, commit the verifier/test changes on `codex/issue-221`, and leave the workspace ready for the next supervisor phase.
- Verification gap: none for the scoped verifier changes; focused tests, direct verifier runs, and one explicit negative check all passed.
- Files touched: .codex-supervisor/issues/221/issue-journal.md; scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh; scripts/test-verify-control-plane-state-model-doc.sh; scripts/test-verify-phase-10-thesis-consistency.sh; scripts/verify-readme-and-repository-structure-control-plane-thesis.sh; scripts/verify-control-plane-state-model-doc.sh
- Rollback concern: Low; changes are isolated to Phase 10 thesis verifier deny-lists and their focused regression tests.
- Last focused command: `tmpdir=$(mktemp -d) ... bash scripts/verify-readme-and-repository-structure-control-plane-thesis.sh "$tmpdir/repo"`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
