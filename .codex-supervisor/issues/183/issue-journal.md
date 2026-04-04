# Issue #183: implementation: materialize control-plane schema v1 from the reviewed placeholders

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/183
- Branch: codex/issue-183
- Workspace: .
- Journal: .codex-supervisor/issues/183/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 62acbd4363a69fc5074d10175f92e4f8f2f6fe00
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T21:18:46.765Z

## Latest Codex Summary
- Reproduced the mismatch by tightening `scripts/verify-control-plane-schema-skeleton.sh` to require a materialized v1 schema baseline; the pre-change repo failed immediately on the placeholder README contract.
- Replaced the placeholder `postgres/control-plane/` assets with a reviewed v1 baseline covering the approved control-plane record families plus explicit reconciliation linkage.
- Updated adjacent repository docs and the Phase 8 foundation validation layer so the repo no longer reasserts the superseded placeholder-only contract.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue #183 is satisfied by replacing the placeholder-only control-plane SQL contract with a repository-validated v1 baseline that preserves the n8n ownership split and explicit reconciliation state.
- What changed: Materialized executable schema and migration DDL for the 12 approved control-plane record families; rewrote the focused schema verifier/tests to require the v1 baseline; updated README, repository-structure, state-model, and Phase 8 validation artifacts to match the advanced contract.
- Current blocker: None.
- Next exact step: Stage the schema/doc/script changes, commit a coherent checkpoint on `codex/issue-183`, and leave the branch ready for review.
- Verification gap: `psql` is not installed in this workspace, so SQL was validated through repository verifiers and shell tests rather than an actual PostgreSQL parser/runtime.
- Files touched: README.md; docs/control-plane-state-model.md; docs/repository-structure-baseline.md; docs/phase-8-control-plane-foundation-validation.md; postgres/control-plane/README.md; postgres/control-plane/schema.sql; postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql; scripts/verify-control-plane-schema-skeleton.sh; scripts/test-verify-control-plane-schema-skeleton.sh; scripts/verify-phase-8-control-plane-foundation-validation.sh; scripts/test-verify-phase-8-control-plane-foundation-validation.sh
- Rollback concern: The main risk is contract drift for downstream work that still assumes placeholder-only SQL assets; the aligned verification/docs updates were included specifically to avoid that split-brain state.
- Last focused command: bash scripts/test-verify-phase-8-control-plane-foundation-validation.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
