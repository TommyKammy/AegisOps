# Issue #125: implementation: add normalized telemetry fixtures and field-coverage verification for the selected telemetry family

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/125
- Branch: codex/issue-125
- Workspace: .
- Journal: .codex-supervisor/issues/125/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 4305a01bc128c81a2885e9332057f79d37a68efa
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-03T04:11:53.483Z

## Latest Codex Summary
- Added explicit Windows field-coverage verification for the selected Phase 6 telemetry family, tightened the focused verifier test to reproduce the missing coverage section first, and updated the Windows onboarding package plus verifier checks to validate required, optional, unavailable, deferred, and exception-path coverage against the normalized fixtures.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The Windows onboarding assets already contained representative replay fixtures, but the repository lacked a focused verifier that proved the reviewed normalized examples explicitly covered the Windows family field-coverage categories required by the source-onboarding contract.
- What changed: Added a reproducing failure to `scripts/test-verify-windows-source-onboarding-assets.sh`, expanded `scripts/verify-windows-source-onboarding-assets.sh` to require a field-coverage verification section and concrete normalized-field evidence, and updated `docs/source-families/windows-security-and-endpoint/onboarding-package.md` with an explicit coverage matrix and exception-path language.
- Current blocker: none
- Next exact step: Commit the verified Windows field-coverage slice on `codex/issue-125` and continue only if follow-on supervisor work requests broader Phase 6 validation.
- Verification gap: No broader Phase 6 detector or replay workflow checks were run in this turn; verification stayed limited to the Windows onboarding verifier plus the canonical schema and source-onboarding contract scripts.
- Files touched: docs/source-families/windows-security-and-endpoint/onboarding-package.md; scripts/verify-windows-source-onboarding-assets.sh; scripts/test-verify-windows-source-onboarding-assets.sh
- Rollback concern: Low; changes are limited to review documentation and shell verifiers for Windows onboarding assets.
- Last focused command: bash scripts/verify-source-onboarding-contract-doc.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproduced the gap by adding a failing case that required `## 5. Field Coverage Verification`; the old verifier then failed before implementation updated section numbering and coverage checks.
