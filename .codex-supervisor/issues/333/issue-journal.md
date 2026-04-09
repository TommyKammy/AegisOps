# Issue #333: design: define the cited advisory-output contract on top of assistant-context snapshots

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/333
- Branch: codex/issue-333
- Workspace: .
- Journal: .codex-supervisor/issues/333/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 58c2a3f02469c1c663a65d79c0f829fb10d3700d
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T09:21:31.318Z

## Latest Codex Summary
- Added a focused failing Phase 15 doc test for the missing assistant-context snapshot advisory-output contract, then updated the boundary, operating guidance, validation record, and verification script so the contract is defined and guarded locally.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The current Phase 15 docs already covered grounding and advisory-only constraints, but they did not define the cited advisory-output contract rendered from assistant-context snapshots or fail-closed rendering conditions for missing citations, conflicting reviewed context, and unresolved identity ambiguity.
- What changed: Added focused unittest coverage for the missing contract, reproduced the gap with a red test, then updated the Phase 15 boundary doc with a structured advisory-output contract and fail-closed rendering rules; aligned the operating guidance and validation record; and tightened the Phase 15 verification script to assert the new contract text and test names.
- Current blocker: none
- Next exact step: Commit the checkpointed doc and test changes on `codex/issue-333`, then decide whether to open a draft PR for the coherent design slice.
- Verification gap: Focused verification passed locally, but the broader repository test suite and CI workflow were not rerun in this turn.
- Files touched: `control-plane/tests/test_phase15_identity_grounded_analyst_assistant_boundary_docs.py`, `docs/phase-15-identity-grounded-analyst-assistant-boundary.md`, `docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md`, `docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md`, `scripts/verify-phase-15-identity-grounded-analyst-assistant-boundary.sh`
- Rollback concern: low; this slice is documentation and verification-only, but the verification script now depends on the exact contract wording and will need coordinated updates if the reviewed phrasing changes again.
- Last focused command: `bash scripts/verify-phase-15-identity-grounded-analyst-assistant-boundary.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
