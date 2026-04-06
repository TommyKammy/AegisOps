# Issue #241: documentation: align control-plane state-model and verifiers with the vendor-neutral execution-surface contract

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/241
- Branch: codex/issue-241
- Workspace: .
- Journal: .codex-supervisor/issues/241/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 62bff1afa6487e64e9a862665943559f0601e95b
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-06T13:17:33.453Z

## Latest Codex Summary
- Reproduced the issue by tightening `scripts/test-verify-control-plane-state-model-doc.sh` to fail on stale n8n-only execution-surface wording before updating the docs or verifiers.
- Updated `docs/control-plane-state-model.md` so `Action Execution` and related reconciliation language describe reviewed automation-substrate or executor surfaces instead of an n8n-only execution model, while preserving the control-plane versus downstream runtime ownership split.
- Updated `scripts/verify-control-plane-state-model-doc.sh`, `scripts/verify-phase-11-control-plane-ci-validation.sh`, and their shell tests to fail closed on stale n8n-only wording in the reviewed boundary docs.
- Verified with the focused shell guards plus the requested unit tests and verifier scripts.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The Phase 11 runtime and service tests already model vendor-neutral execution surfaces, but the reviewed control-plane state-model doc and shell verifiers still preserved stale n8n-only `Action Execution` and reconciliation wording.
- What changed: Added a failing-first shell-test case for stale n8n-only wording, rewrote the state-model language to describe reviewed automation-substrate and executor surfaces, and tightened both verifier scripts plus both shell-test guards to require the new wording.
- Current blocker: none
- Next exact step: Stage the doc and verifier changes, commit the checkpoint on `codex/issue-241`, and leave the branch ready for PR creation or supervisor follow-up.
- Verification gap: none for the updated docs and focused verifiers; broader repo-wide verification was not needed for this documentation-only scope.
- Files touched: docs/control-plane-state-model.md; docs/phase-11-control-plane-ci-validation.md; scripts/verify-control-plane-state-model-doc.sh; scripts/test-verify-control-plane-state-model-doc.sh; scripts/verify-phase-11-control-plane-ci-validation.sh; scripts/test-verify-phase-11-control-plane-ci-validation.sh; .codex-supervisor/issues/241/issue-journal.md
- Rollback concern: Low; changes are limited to reviewed documentation text and fail-closed verifier expectations around the same boundary.
- Last focused command: python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection control-plane.tests.test_postgres_store
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
