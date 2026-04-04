# Issue #181: design: define the control-plane runtime service boundary and repository placement

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/181
- Branch: codex/issue-181
- Workspace: .
- Journal: .codex-supervisor/issues/181/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 52e68c0321d2a5853bca9d79c3e3012dfc57f9e4
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T20:07:19.511Z

## Latest Codex Summary
- Reproduced the issue as a documentation-and-verification gap: existing repository checks passed, but no reviewed artifact defined the live control-plane runtime boundary or repository placement for application code.
- Added a dedicated Phase 9 design reference, approved `control-plane/` as the live runtime home, kept `postgres/control-plane/` as the persistence-contract home, and tightened repository/validation scripts to fail closed on that split.
- Focused verification now passes for the new runtime-boundary verifier, the updated repository structure and skeleton verifiers, the Phase 9 validation record, and the targeted test scripts.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The missing deliverable was not a failing implementation test but an absent design-and-verification contract for where the first live control-plane service belongs and how it stays separate from OpenSearch, n8n, and `postgres/control-plane/`.
- What changed: Added `docs/control-plane-runtime-service-boundary.md`, `control-plane/README.md`, `docs/phase-9-control-plane-runtime-boundary-validation.md`, new verifier/test scripts for the boundary, and updated `README.md`, `docs/architecture.md`, `docs/repository-structure-baseline.md`, repository skeleton docs/scripts, and the documentation ownership map to approve and enforce the new `control-plane/` top-level runtime home.
- Current blocker: none
- Next exact step: Commit the staged Phase 9 control-plane runtime-boundary checkpoint, then report the verified placement and scope contract back to the supervisor.
- Verification gap: No broad repo-wide test sweep was run because the change is documentation and verification-script scoped; focused checks for the affected contract passed.
- Files touched: README.md; control-plane/README.md; docs/architecture.md; docs/control-plane-runtime-service-boundary.md; docs/documentation-ownership-map.md; docs/phase-9-control-plane-runtime-boundary-validation.md; docs/repository-skeleton-validation.md; docs/repository-structure-baseline.md; scripts/test-verify-control-plane-runtime-service-boundary-doc.sh; scripts/test-verify-repository-skeleton.sh; scripts/verify-control-plane-runtime-service-boundary-doc.sh; scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh; scripts/verify-repository-skeleton.sh; scripts/verify-repository-structure-doc.sh
- Rollback concern: Reverting this checkpoint would remove the newly approved top-level `control-plane/` repository placement and make later Phase 9 runtime scaffolding ambiguous again.
- Last focused command: bash scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
