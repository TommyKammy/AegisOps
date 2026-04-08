# Issue #315: implementation: add a forward PostgreSQL migration path for Phase 14 reviewed_context fields

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/315
- Branch: codex/issue-315
- Workspace: .
- Journal: .codex-supervisor/issues/315/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 6 (implementation=2, repair=4)
- Last head SHA: eca4e854ff63470ba7559d707b39465f529d7d07
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-08T22:06:04.540Z

## Latest Codex Summary
Adjusted the Phase 8 test fixture so `0002_phase_14_reviewed_context_columns.sql` is no longer part of the baseline artifact set, while still being layered into every fixture that needs to satisfy the current verifier chain. The change is in [scripts/test-verify-phase-8-control-plane-foundation-validation.sh](scripts/test-verify-phase-8-control-plane-foundation-validation.sh#L16-L53) and the fixture setup block at [lines 114-167](scripts/test-verify-phase-8-control-plane-foundation-validation.sh#L114-L167).

Verified the repair slice with `bash scripts/test-verify-phase-8-control-plane-foundation-validation.sh`, `python3 -m unittest control-plane.tests.test_postgres_store`, and `bash scripts/test-verify-control-plane-schema-skeleton.sh`; all three passed on the current workspace state.

Summary: Separated the Phase 8 test fixture baseline from the Phase 14 forward migration asset so the phase-8 contract stays narrow while the current verifier chain still passes.
State hint: local_review_fix
Blocked reason: none
Tests: `bash scripts/test-verify-phase-8-control-plane-foundation-validation.sh`, `python3 -m unittest control-plane.tests.test_postgres_store`, `bash scripts/test-verify-control-plane-schema-skeleton.sh`
Next action: Await re-review or CI on PR `#317`; no further local repair needed for this slice
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: the Phase 8 fixture should keep `postgres/control-plane/migrations/0002_phase_14_reviewed_context_columns.sql` out of the baseline artifact set and layer it in separately for the verifier chain.
- What changed: Removed `0002_phase_14_reviewed_context_columns.sql` from the Phase 8 baseline artifact array and copied it into each fixture via a dedicated helper so the verifier still sees the forward migration without coupling it to the baseline list.
- Current blocker: None.
- Next exact step: none; this repair slice is complete.
- Verification gap: None remaining for this repair slice.
- Files touched: `scripts/test-verify-phase-8-control-plane-foundation-validation.sh`.
- Rollback concern: Re-adding `0002_phase_14_reviewed_context_columns.sql` to the baseline artifact array would re-couple the Phase 8 contract to the Phase 14 migration asset.
- Last focused commands: `bash scripts/test-verify-phase-8-control-plane-foundation-validation.sh`, `python3 -m unittest control-plane.tests.test_postgres_store`, `bash scripts/test-verify-control-plane-schema-skeleton.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
