# Issue #124: implementation: add source onboarding assets and replay fixtures for the selected telemetry family

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/124
- Branch: codex/issue-124
- Workspace: .
- Journal: .codex-supervisor/issues/124/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 9681b3b7c0c46c05c68d685c25bc70ac0d8181e2
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-03T03:57:16.455Z

## Latest Codex Summary
- Added a focused verifier and shell test for Windows source onboarding assets and replay fixtures, reproduced the missing-package failure, then added the Windows onboarding package and reviewed replay corpus under `docs/source-families/` and `ingest/replay/`.
- Focused verification now passes for the new verifier and adjacent Phase 6/source-onboarding checks.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The repo was missing the selected Windows source-family onboarding package and replay fixtures needed for Phase 6 source-readiness review.
- What changed: Added `scripts/verify-windows-source-onboarding-assets.sh` and `scripts/test-verify-windows-source-onboarding-assets.sh`, wired them into `.github/workflows/ci.yml`, and created the Windows onboarding package plus raw and normalized replay fixtures.
- Current blocker: none
- Next exact step: Review the new Windows onboarding assets, then stage and commit the focused checkpoint on `codex/issue-124`.
- Verification gap: Full CI was not run locally; focused verification only.
- Files touched: `.github/workflows/ci.yml`, `scripts/verify-windows-source-onboarding-assets.sh`, `scripts/test-verify-windows-source-onboarding-assets.sh`, `docs/source-families/windows-security-and-endpoint/onboarding-package.md`, `ingest/replay/windows-security-and-endpoint/README.md`, `ingest/replay/windows-security-and-endpoint/raw/*`, `ingest/replay/windows-security-and-endpoint/normalized/*`
- Rollback concern: Low; changes are additive docs, fixtures, and verification only.
- Last focused command: `bash scripts/test-verify-ci-phase-5-workflow-coverage.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
